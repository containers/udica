#!/bin/bash

set -eo pipefail

source $(dirname $0)/lib.sh

req_env_vars GOPATH SCRIPT_BASE CIRRUS_WORKING_DIR PODMAN_FROM OS_RELEASE_ID

[[ "$PODMAN_FROM" == 'main' ]] || \
    die 1 "Unsupported \$PODMAN_FROM value: $PODMAN_FROM"

remove_packaged_podman_files

echo "Building & installing libpod from '$PODMAN_FROM' source"
GOSRC=$GOPATH/src/github.com/containers/libpod
mkdir -p "$GOSRC"
showrun git clone -b "$PODMAN_FROM" https://github.com/containers/libpod.git "$GOSRC"
cd "$GOSRC"
showrun make
showrun make install PREFIX=/usr ETCDIR=/etc

echo "Configuring podman for execution w/in a container"
sed -e 's|^#mount_program|mount_program|g' \
    -e 's|^mountopt[[:space:]]*=.*$|mountopt = "nodev,fsync=0"|g' \
    /usr/share/containers/storage.conf \
    > /etc/containers/storage.conf
setsebool container_manage_cgroup true  # systemd in container

echo "Installing Udica from source"
cd "$CIRRUS_WORKING_DIR"
showrun python3 ./setup.py install
