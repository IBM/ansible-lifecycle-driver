FROM python:3.7-alpine

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8293}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-gunicorn}

COPY ansible.cfg /etc/ansible/ansible.cfg
COPY whls/*.whl /home/ald/whls/
COPY ald_config.yml /var/ald/ald_config.yml

RUN addgroup -S ald \
 && adduser -S ald -G ald -u 100 \
 && mkdir -p /var/ald/lifecycle_scripts \
 # set group to 0 to allow arbitrary users in OCP to write to these directories 
 && chown -R ald:0 /var/ald \
 && chmod -R 777 /var/ald \
 && chown -R ald:0 /home/ald \
 && chmod -R 775 /home/ald \
 && apk add --no-cache bash openssh sshpass curl binutils libc-dev \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
 && for i in /home/ald/whls/ignition*.whl; do if [ "$i" != "/home/ald/whls/ignition*.whl" ]; then pip install --no-warn-script-location "$i"; fi done \
 && for i in /home/ald/whls/*.whl; do pip install --no-warn-script-location "$i"; done \
 && curl -L https://storage.googleapis.com/kubernetes-release/release/v1.16.0/bin/linux/amd64/kubectl -o /usr/bin/kubectl \
 && chmod 775 /usr/bin/kubectl \
 # clean up packages used to install Python packages
 && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

USER ald
WORKDIR /home/ald

EXPOSE 8293

CMD ["ald"]