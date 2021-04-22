## Docker image

This is a Docker image used to run storm-info-provider tests.

### Usage

Build image:

    sh build-image.sh

Then, run it:

    docker run italiangrid/storm-info-provider:latest

You can select the repo branch by setting the environment variable `GIT_BRANCH`.
Example:

    docker run -e GIT_BRANCH=fix/STOR-982 italiangrid/storm-info-provider:latest