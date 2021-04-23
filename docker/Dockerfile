FROM centos:7

ENV GIT_BRANCH develop
ENV PYTHON_VERSION 3.9.2
ENV PYTHON_COMMAND python3.9

RUN yum install -y epel-release
RUN yum groupinstall -y "Development tools"
RUN yum install -y gcc make openssl-devel bzip2-devel libffi-devel wget git
RUN yum install -y openldap-devel python-devel libsqlite3x-devel sqlite-devel

RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz && \
    tar xzf Python-$PYTHON_VERSION.tgz && \
    cd Python-$PYTHON_VERSION && \
    ./configure --enable-optimizations && \
    make altinstall

RUN rm -f /usr/src/Python-$PYTHON_VERSION.tgz

RUN $PYTHON_COMMAND -V
RUN python -V

# Install pip 
RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN $PYTHON_COMMAND get-pip.py

RUN $PYTHON_COMMAND -m pip install mock coverage unittest2 python-ldap

COPY ./build.sh build.sh
RUN chmod +x build.sh

CMD sh build.sh

