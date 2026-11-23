terraform {
  required_version = ">= 1.5"
}

variable "cluster_name" {
  description = "Name of the kind cluster"
  type        = string
  default     = "capstone"
}

locals {
  kind_config = "${path.module}/../../../k8s/kind-config.yaml"
}

# Creates the kind cluster only if it does not exist yet, and deletes it on destroy.
resource "terraform_data" "kind_cluster" {
  input = {
    name   = var.cluster_name
    config = local.kind_config
  }

  provisioner "local-exec" {
    command = "kind get clusters | grep -qx ${self.input.name} || kind create cluster --config ${self.input.config}"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "kind delete cluster --name ${self.input.name}"
  }
}

output "kube_context" {
  value = "kind-${var.cluster_name}"
}
