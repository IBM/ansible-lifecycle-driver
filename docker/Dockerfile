FROM python:3.7-alpine

ARG DRIVER_PORT
ENV DRIVER_PORT ${DRIVER_PORT:-8293}
ARG NUM_PROCESSES
ENV NUM_PROCESSES ${NUM_PROCESSES:-4}
ARG NUM_THREADS
ENV NUM_THREADS ${NUM_THREADS:-2}
ARG WSGI_CONTAINER
ENV WSGI_CONTAINER ${WSGI_CONTAINER:-uwsgi}

ENV PATH="/home/ald/.local/bin:${PATH}"
COPY ansible.cfg /etc/ansible/ansible.cfg

RUN addgroup -S ald \
 && adduser -S ald -G ald \
 && mkdir -p /var/ald/lifecycle_scripts \
 && chown -R ald:ald /var/ald \
 && apk add --no-cache bash openssh sshpass \
 # These packages need to be installed so that we can install the Python dependencies.
 # We make this virtual so that we can remove them later
 && apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

USER ald

COPY --chown=ald:ald whls/*.whl /home/ald/whls/
COPY --chown=ald:ald ald_config.yml /var/ansible-lifecycle-driver/ald_config.yml

RUN for i in /home/ald/whls/*.whl; do pip install --no-warn-script-location --user "$i"; done

USER root

RUN apk del .build-deps gcc musl-dev libffi-dev openssl-dev python3-dev make git

USER ald
WORKDIR /home/ald

EXPOSE 8293

CMD ["ald"]