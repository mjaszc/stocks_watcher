#!/bin/sh

export $(grep -v '^#' ../../.env.staging | xargs)

docker build --no-cache -t $DOCKER_IMAGE_BACKEND ..
docker build --no-cache -t $DOCKER_IMAGE_FRONTEND ../../frontend/

docker compose -f ../../docker-compose.staging.yml --env-file ../../.env.staging up --build --remove-orphans