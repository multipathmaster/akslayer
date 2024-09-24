#!/bin/bash
ENVIRONMENT="Stage"
clusterName=`kubectl config current-context --insecure-skip-tls-verify`
sleep 4
kubectl get nodes -o wide | grep -v NAME | awk '{ print $1 }' > stage/$clusterName.$ENVIRONMENT.nodes
