#!/bin/sh

export $(grep -v '^#' ../../.env.local | xargs)

docker build --no-cache -t $DOCKER_IMAGE_BACKEND:latest ..
docker build --no-cache -t $DOCKER_IMAGE_FRONTEND:latest ../../frontend/

docker compose -f ../../docker-compose.dev.yml --env-file ../../.env.local up --build --remove-orphans