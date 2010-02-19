#!/bin/sh
if [ ! -d ./RPMS ]; then
    mkdir RPMS
fi

if [ ! -d ./RPMS/BUILD ]; then
    mkdir ./RPMS/BUILD
fi

if [ ! -d ./RPMS/RPMS ]; then
    mkdir ./RPMS/RPMS
fi

if [ ! -d ./RPMS/SOURCES ]; then
    mkdir ./RPMS/SOURCES
fi

if [ ! -d ./RPMS/SPECS ]; then
    mkdir ./RPMS/SPECS
fi

if [ ! -d ./RPMS/SRPMS ]; then
    mkdir ./RPMS/SRPMS
fi

# Retrieving version from spec file
VERSION=`cat ./rpm/glite-info-dynamic-storm.spec | grep "Version:" | awk '{ print $2 }'`

echo "Building RPMs for version: $VERSION (retrieved from spec file: "./rpm/glite-info-dynamic-storm.spec")"

if [ -z $VERSION ]; then 
    echo "Unable to retrieve the version from the spec file"
    exit 1
fi

# Get sources
ant -Dversion=$VERSION info.src

CUR_DIR=`pwd`

cp $CUR_DIR/rpm/glite-info-dynamic-storm.spec $CUR_DIR/RPMS/SPECS/glite-info-dynamic-storm.spec
cp glite-info-dynamic-storm-$VERSION.tar.gz ./RPMS/SOURCES/

# Generate RPMs
if [ $ARCH_BIT == 64 ]; then
    rpmbuild --define "_topdir $CUR_DIR/RPMS" --define "arch_bit 64" -ba $CUR_DIR/RPMS/SPECS/glite-info-dynamic-storm.spec
else
    rpmbuild --define "_topdir $CUR_DIR/RPMS" -ba $CUR_DIR/RPMS/SPECS/glite-info-dynamic-storm.spec
fi

