FROM python:3.7-alpine

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8293}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-gunicorn}

ENV PATH="/home/ald/.local/bin:${PATH}"

RUN addgroup -S ald -g 1000 \
 && adduser -S ald -G ald -u 1000 \
 && mkdir -p /var/ald/lifecycle_scripts \
 && apk add --no-cache bash openssh sshpass curl binutils libc-dev \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

USER ald

COPY --chown=ald:0 ansible.cfg /etc/ansible/ansible.cfg
COPY --chown=ald:0 whls/*.whl /home/ald/whls/
COPY --chown=ald:0 ald_config.yml /var/ald/ald_config.yml 

RUN for i in /home/ald/whls/ignition*.whl; do if [ "$i" != "/home/ald/whls/ignition*.whl" ]; then pip install --no-warn-script-location --user "$i"; fi done \
 && for i in /home/ald/whls/*.whl; do pip install --no-warn-script-location --user "$i"; done \
 && curl -L https://storage.googleapis.com/kubernetes-release/release/v1.16.0/bin/linux/amd64/kubectl -o /home/ald/.local/bin/kubectl \
 && chmod +x /home/ald/.local/bin/kubectl

USER root

# clean up packages used to install Python packages
RUN apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
 && chown -R ald:0 /home/ald \
 && chown -R ald:0 /var/ald \
 && chmod -R 775 /home/ald \
 && chmod -R 775 /var/ald \
 && ls -al /home/ald/.local/lib/python3.7 \
 && ls -al /home/ald/.local/bin \
 && whoami \
 && cat /etc/passwd

EXPOSE 8293

USER ald
WORKDIR /home/ald

CMD ["ald"]