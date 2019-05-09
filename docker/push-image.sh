#!/bin/bash
set -ex

tag=${tag:-"latest"}

if [ -n "${DOCKER_REGISTRY_HOST}" ]; then
  docker tag italiangrid/storm-info-provider:${tag} ${DOCKER_REGISTRY_HOST}/italiangrid/storm-info-provider:${tag}
  docker push ${DOCKER_REGISTRY_HOST}/italiangrid/storm-info-provider:${tag}
fi
