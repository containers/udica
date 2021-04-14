#!/bin/bash

set -eo pipefail

source "$(dirname $0)/lib.sh"

show_env_vars

case "${OS_RELEASE_ID}" in
    fedora)
        echo "Installing necessary additional packages"
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
# helpful when debugging w/ hack/get_ci_vm.sh
git config --global --replace-all remote.upstream.fetch "$NEWREF"
