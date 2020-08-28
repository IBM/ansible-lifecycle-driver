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
COPY ansible.cfg /etc/ansible/ansible.cfg

RUN addgroup -S ald \
 && adduser -S ald -G ald -u 100 \
 && mkdir -p /var/ald/lifecycle_scripts \
 && chown -R ald:ald /var/ald \
 && chown -R ald:ald /home/ald \
 && apk add --no-cache bash openssh sshpass curl binutils libc-dev \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

USER ald

COPY --chown=ald:ald extra-requirements.txt /home/ald/extra-requirements.txt
COPY --chown=ald:ald whls/*.whl /home/ald/whls/
COPY --chown=ald:ald ald_config.yml /var/ald/ald_config.yml
COPY --chown=ald:ald library /etc/ansible/library
COPY --chown=ald:ald module_utils /etc/ansible/module_utils
COPY --chown=ald:ald roles /etc/ansible/roles

RUN for i in /home/ald/whls/ignition*.whl; do if [ "$i" != "/home/ald/whls/ignition*.whl" ]; then pip install --no-warn-script-location --user "$i"; fi done \
 && for i in /home/ald/whls/*.whl; do pip install --no-warn-script-location --user "$i"; done \
 && curl -L https://storage.googleapis.com/kubernetes-release/release/v1.16.0/bin/linux/amd64/kubectl -o /home/ald/.local/bin/kubectl \
 && chmod +x /home/ald/.local/bin/kubectl

# Install extra requirements to be built into the driver
RUN pip install -r /home/ald/extra-requirements.txt

USER root

# clean up packages used to install Python packages
RUN apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

EXPOSE 8293

USER ald
WORKDIR /home/ald

CMD ["ald"]