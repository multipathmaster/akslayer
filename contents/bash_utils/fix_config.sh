#!/bin/bash
sed -i 's/certificate-authority-data.*/insecure-skip-tls-verify: true/g' /root/.kube/config
