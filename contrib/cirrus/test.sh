#!/bin/bash

set -eo pipefail

source $(dirname $0)/lib.sh

req_env_vars GOPATH SCRIPT_BASE CIRRUS_WORKING_DIR PODMAN_FROM

showrun python3 -m udica --help

showrun podman run -d -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 fedora sleep 1h

echo "Running podman inspect -l"
podman inspect -l > /tmp/container.json

showrun udica -j /tmp/container.json my_container
