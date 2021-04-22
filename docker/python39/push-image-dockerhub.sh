#!/bin/bash
set -ex

tag=${tag:-"latest"}

echo "Pushing italiangrid/storm-info-provider:${tag} on dockerhub ..."
docker push italiangrid/storm-info-provider:${tag}
