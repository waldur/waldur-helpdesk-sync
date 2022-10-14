# Use to avoid pull rate limit for Docker Hub images
ARG DOCKER_REGISTRY=docker.io/
FROM ${DOCKER_REGISTRY}library/python:3.9

COPY . /usr/src/waldur-helpdesk-sync

WORKDIR /usr/src/waldur-helpdesk-sync
RUN pip install -r requirements.txt --no-cache-dir

CMD [ "python", "waldur_helpdesk_sync/main.py" ]
