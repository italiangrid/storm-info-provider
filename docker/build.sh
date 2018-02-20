#!/bin/bash

git clone https://github.com/italiangrid/storm-info-provider.git -b ${GIT_BRANCH}
cd storm-info-provider/src
coverage run --source=. -m unittest discover