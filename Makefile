.RECIPEPREFIX = >
ANSIBLE = ansible-playbook -i ansible/inventory.ini ansible/site.yml
TF = terraform
.PHONY: help up down tools cluster platform deploy status

help:
> @echo "make up        build everything: tools, cluster, platform, app"
> @echo "make down      destroy the platform and the cluster"
> @echo "make status    show nodes and pods"
> @echo "make tools | cluster | platform | deploy   run a single stage"

up: tools cluster platform deploy

tools:
> $(ANSIBLE) --tags tools

cluster:
> cd infra/terraform/cluster && $(TF) init -input=false && $(TF) apply -auto-approve -input=false

platform:
> cd infra/terraform/platform && $(TF) init -input=false && $(TF) apply -auto-approve -input=false

deploy:
> $(ANSIBLE) --tags deploy

status:
> kubectl get nodes
> kubectl -n notes get pods -o wide

down:
> -cd infra/terraform/platform && $(TF) destroy -auto-approve -input=false
> cd infra/terraform/cluster && $(TF) destroy -auto-approve -input=false
