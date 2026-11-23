import datetime
import os

os.environ["SKIP_DB_INIT"] = "1"

import pytest  # noqa: E402

import app as app_module  # noqa: E402


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_version(client):
    assert "version" in client.get("/version").get_json()


def test_add_note_rejects_empty_text(client):
    response = client.post("/api/notes", json={"text": "   "})
    assert response.status_code == 400


def test_add_note_success(client, monkeypatch):
    monkeypatch.setattr(app_module, "query", lambda *args, **kwargs: None)
    response = client.post("/api/notes", json={"text": "hello"})
    assert response.status_code == 201


def test_list_notes(client, monkeypatch):
    rows = [(1, "hello", datetime.datetime(2026, 1, 1, 10, 0))]
    monkeypatch.setattr(app_module, "query", lambda *args, **kwargs: rows)
    response = client.get("/api/notes")
    assert response.get_json()[0]["text"] == "hello"


def test_ready_returns_503_when_database_is_down(client, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr(app_module, "query", broken)
    assert client.get("/ready").status_code == 503


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert b"http_requests_total" in response.data
