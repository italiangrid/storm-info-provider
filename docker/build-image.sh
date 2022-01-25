#!/bin/bash

tag=${tag:-"latest"}

docker build --pull=false --no-cache --rm=true -t italiangrid/storm-info-provider:${tag} .
