FROM python:3.10-alpine
RUN apk update && apk upgrade \
    && rm -rf /var/cache/apk/*

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8293}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}

COPY whls/*.whl /whls/

RUN addgroup -S ald \
    && adduser -S ald -G ald -u 101 \
    && mkdir -p /var/ald/lifecycle_scripts \
    && chown -R ald:0 /var/ald \
    && chmod -R 775 /var/ald \
    && chown -R ald:0 /home/ald \
    && chmod -R 775 /home/ald \
    && apk add --no-cache bash openssh sshpass curl binutils libc-dev expect \
    # These packages need to be installed so that we can install the Python dependencies.
    # We make this virtual so that we can remove them later
    && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git cargo \
    && pip install --upgrade pip \
    && for i in /whls/ignition*.whl; do if [ "$i" != "/whls/ignition*.whl" ]; then pip install --no-warn-script-location "$i"; fi done \
    && for i in /whls/*.whl; do pip install "$i"; done \
    && rm -rf /usr/local/lib/python3.10/site-packages/ansible_collections/azure/azcollection \
    && wget https://galaxy.ansible.com/download/azure-azcollection-1.14.0.tar.gz -P /tmp/ \
    && ansible-galaxy collection install /tmp/azure-azcollection-1.14.0.tar.gz --force -p /usr/local/lib/python3.10/site-packages/ansible_collections \
    && pip install --no-cache-dir -r /usr/local/lib/python3.10/site-packages/ansible_collections/azure/azcollection/requirements-azure.txt \
    && ansible-galaxy collection install ansible.utils -f -p /usr/local/lib/python3.10/site-packages/ansible_collections \
    && pip install netaddr \
    && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
    && curl -L https://storage.googleapis.com/kubernetes-release/release/v1.32.1/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl

COPY --chown=ald:0 ansible.cfg /etc/ansible/ansible.cfg
COPY --chown=ald:0 ald_config.yml /var/ald/ald_config.yml

RUN cp /usr/local/lib/python3.10/site-packages/ansibledriver/ibm_cp4na_log_message.py /usr/local/lib/python3.10/site-packages/ansible/modules

# Set HOME variable for OCP arbitrary user
ENV HOME /home/ald

USER ald
WORKDIR /home/ald

EXPOSE 8293

CMD SSL="--certfile /var/ald/certs/tls.crt --keyfile /var/ald/certs/tls.key" && if [ $SSL_DISABLED ]; then SSL="" ; fi \
    && gunicorn -k uvicorn.workers.UvicornWorker --workers $NUM_PROCESSES --bind [::]:$DRIVER_PORT $SSL "ansibledriver:create_wsgi_app()"
