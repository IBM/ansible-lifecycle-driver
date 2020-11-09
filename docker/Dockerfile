FROM python:3.7-alpine

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8293}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-gunicorn}

COPY whls/*.whl /whls/

RUN addgroup -S ald \
 && adduser -S ald -G ald -u 100 \
 && mkdir -p /var/ald/lifecycle_scripts \
 && chown -R ald:0 /var/ald \
 && chmod -R 775 /var/ald \
 && chown -R ald:0 /home/ald \
 && chmod -R 775 /home/ald \
 && apk add --no-cache bash openssh sshpass curl binutils libc-dev \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
 && for i in /whls/ignition*.whl; do if [ "$i" != "/whls/ignition*.whl" ]; then pip install --no-warn-script-location "$i"; fi done \
 && for i in /whls/*.whl; do pip install "$i"; done \
 && apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git \
 && curl -L https://storage.googleapis.com/kubernetes-release/release/v1.19.0/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl \
 && chmod +x /usr/local/bin/kubectl

COPY --chown=ald:0 extra-requirements.txt /home/ald/extra-requirements.txt
COPY --chown=ald:0 ansible.cfg /etc/ansible/ansible.cfg
COPY --chown=ald:0 ald_config.yml /var/ald/ald_config.yml 
COPY --chown=ald:0 library /etc/ansible/library
COPY --chown=ald:0 module_utils /etc/ansible/module_utils
COPY --chown=ald:0 roles /etc/ansible/roles

# Install extra requirements to be built into the driver
RUN pip install -r /home/ald/extra-requirements.txt

# Set HOME variable for OCP arbitrary user
ENV HOME /home/ald

USER ald
WORKDIR /home/ald

EXPOSE 8293

CMD ["ald"]
