#!/bin/bash

tag=${tag:-"latest"}

docker build --pull=false --rm=true -t italiangrid/storm-info-provider:${tag} .
