FROM python:3.7-alpine

ARG PYPI_REPO_IP
ENV PYPI_REPO_IP ${PYPI_REPO_IP:-nexus.accanto.com}
ARG PYPI_REPO_PORT
ENV PYPI_REPO_PORT ${PYPI_REPO_PORT:-8081}
ARG PYPI_REPO_URI
ENV PYPI_REPO_URI ${PYPI_REPO_URI:-http://$PYPI_REPO_IP:$PYPI_REPO_PORT/repository/pypi/simple}
ARG DRIVER_VERSION
ENV DRIVER_VERSION ${DRIVER_VERSION:-0.1.0.dev0}
ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8293}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-uwsgi}

COPY ansibledriver/config/ansible.cfg /etc/ansible/ansible.cfg

# copy any Ansible driver config overrides to Docker container
COPY docker/ald_config.yml /var/ansible-lifecycle-driver/ald_config.yml

RUN addgroup -S ald \
 && adduser -S ald -G ald \
 && mkdir -p /var/ald/lifecycle_scripts \
 && chown -R ald:ald /var/ald \
 && apk add --no-cache bash openssh sshpass \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make \
 && pip3 install --trusted-host $PYPI_REPO_IP --extra-index-url $PYPI_REPO_URI ansible-lifecycle-driver==$DRIVER_VERSION \
 && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make 

USER ald
WORKDIR /home/ald

EXPOSE 8293

CMD ["ald"]