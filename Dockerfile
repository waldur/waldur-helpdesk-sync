# Use to avoid pull rate limit for Docker Hub images
ARG DOCKER_REGISTRY=docker.io/
FROM ${DOCKER_REGISTRY}library/python:3.9

COPY . /usr/src/waldur-rt-sync

WORKDIR /usr/src/waldur-rt-sync
RUN pip install -r requirements.txt --no-cache-dir

CMD [ "python", "waldur_rt_sync/main.py" ]
