FROM mcr.microsoft.com/azure-cli:latest

ENV KUBERNETES_VERSION=1.27.3
RUN yum -y install vi
RUN yum -y install procps
RUN yum -y install awk
RUN yum -y install sed
RUN yum -y install wget
RUN wget https://storage.googleapis.com/kubernetes-release/release/v${KUBERNETES_VERSION}/bin/linux/amd64/kubectl -qO /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl
WORKDIR /usr/local/bin
ADD contents /usr/local/bin/
RUN chmod +x /usr/local/bin/bash_utils/*.sh
ADD docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
RUN yum -y install python3-pip
RUN pip3 install httplib2
RUN pip3 install pygtail
RUN pip3 install flask
RUN pip3 install flask_wtf
RUN pip3 install wtforms
RUN pip3 install psutil
ENTRYPOINT ["docker-entrypoint.sh"]
EXPOSE 80
EXPOSE 8080
EXPOSE 443
EXPOSE 5000
