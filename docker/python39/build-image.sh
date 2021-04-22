#!/bin/bash

tag=${tag:-"python3"}

docker build --pull=false --no-cache --rm=true -t italiangrid/storm-info-provider:${tag} .
