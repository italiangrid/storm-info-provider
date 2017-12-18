FROM python:2.7

ARG GIT_BRANCH=fix/STOR-982

RUN apt-get -y update
RUN apt-get -y install libsasl2-dev python-dev libldap2-dev libssl-dev git
RUN pip install mock unittest2 coverage python-ldap==2.3.13

COPY ./build.sh build.sh
RUN chmod +x build.sh

ENV GIT_BRANCH $GIT_BRANCH

CMD sh build.sh
 