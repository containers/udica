#!/bin/bash

set -eo pipefail

source "$(dirname $0)/lib.sh"

show_env_vars

case "${OS_RELEASE_ID}" in
    fedora)
        msg "Expanding root disk space"
        growpart /dev/sda 1
        resize2fs /dev/sda1
        msg "Installing necessary additional packages"
        ooe.sh dnf install -y \
            python3 \
            setools-console \
            systemd-devel
        ;;
    *) bad_os_id_ver ;;
esac

echo "Configuring git for access to podman pull-requests"
NEWREF='+refs/pull/*/head:refs/remotes/upstream/pr/*'
git config --global --replace-all remote.origin.fetch "$NEWREF"
