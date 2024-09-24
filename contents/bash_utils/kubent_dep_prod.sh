#!/bin/bash
ENVIRONMENT="Production"
clusterName=`kubectl config current-context --insecure-skip-tls-verify`
sleep 4
kubectl get nodes -o wide | grep -v NAME | awk '{ print $1 }' > prod/$clusterName.$ENVIRONMENT.nodes
