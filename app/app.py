import os
import time
import logging
from contextlib import closing

import psycopg2
from flask import Flask, Response, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("notes")

app = Flask(__name__)
APP_VERSION = os.getenv("APP_VERSION", "v1")

DB = {
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "notes"),
    "user": os.getenv("DB_USER", "notes"),
    "password": os.getenv("DB_PASSWORD", "notes"),
}

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency in seconds", ["endpoint"])


def query(sql, params=(), fetch=False):
    with closing(psycopg2.connect(connect_timeout=3, **DB)) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if fetch:
                    return cur.fetchall()


def init_db():
    for _ in range(15):
        try:
            query("CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, text TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW())")
            log.info("database ready")
            return
        except Exception as exc:
            log.warning("waiting for database: %s", exc)
            time.sleep(2)


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def record_metrics(resp):
    endpoint = request.url_rule.rule if request.url_rule else "unknown"
    LATENCY.labels(endpoint).observe(time.time() - getattr(request, "start_time", time.time()))
    REQUESTS.labels(request.method, endpoint, resp.status_code).inc()
    return resp


@app.route("/")
def index():
    return render_template("index.html", version=APP_VERSION)


@app.route("/api/notes", methods=["GET"])
def list_notes():
    rows = query("SELECT id, text, created_at FROM notes ORDER BY id DESC LIMIT 50", fetch=True)
    return jsonify([{"id": r[0], "text": r[1], "created_at": r[2].strftime("%Y-%m-%d %H:%M")} for r in rows])


@app.route("/api/notes", methods=["POST"])
def add_note():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text or len(text) > 500:
        return jsonify({"error": "text is required (max 500 characters)"}), 400
    query("INSERT INTO notes (text) VALUES (%s)", (text,))
    log.info("note added")
    return jsonify({"status": "created"}), 201


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": APP_VERSION})


@app.route("/ready")
def ready():
    try:
        query("SELECT 1", fetch=True)
        return jsonify({"status": "ready"})
    except Exception as exc:
        log.error("not ready: %s", exc)
        return jsonify({"status": "not ready"}), 503


@app.route("/version")
def version():
    return jsonify({"version": APP_VERSION})


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


if os.getenv("SKIP_DB_INIT") != "1":
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
