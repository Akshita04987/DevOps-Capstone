terraform {
  required_version = ">= 1.5"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.30"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }
}

variable "kube_context" {
  description = "kubectl context of the target cluster"
  type        = string
  default     = "kind-capstone"
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.kube_context
}

resource "kubernetes_namespace_v1" "notes" {
  metadata {
    name = "notes"
    labels = {
      "app.kubernetes.io/part-of" = "devops-capstone"
    }
  }
}

resource "kubernetes_namespace_v1" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      "app.kubernetes.io/part-of" = "devops-capstone"
    }
  }
}

# Random database password: never typed by hand and never committed to Git.
resource "random_password" "db" {
  length  = 24
  special = false
}

resource "kubernetes_secret_v1" "db" {
  metadata {
    name      = "db-credentials"
    namespace = kubernetes_namespace_v1.notes.metadata[0].name
  }

  data = {
    username = "notes"
    password = random_password.db.result
    database = "notes"
  }
}
