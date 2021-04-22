#!/bin/bash

tag=${tag:-"python2"}

docker build --pull=false --rm=true -t italiangrid/storm-info-provider:${tag} .
