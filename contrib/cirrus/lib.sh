

# Library of common, shared utility functions.  This file is intended
# to be sourced by other scripts, not called directly.

# BEGIN Global export of all variables
set -a

# Due to differences across platforms and runtime execution environments,
# handling of the (otherwise) default shell setup is non-uniform.  Rather
# than attempt to workaround differences, simply force-load/set required
# items every time this library is utilized.
USER="$(whoami)"
HOME="$(getent passwd $USER | cut -d : -f 6)"
# Some platforms set and make this read-only
[[ -n "$UID" ]] || \
    UID=$(getent passwd $USER | cut -d : -f 3)

# Automation library installed at image-build time,
# defining $AUTOMATION_LIB_PATH in this file.
if [[ -r "/etc/automation_environment" ]]; then
    source /etc/automation_environment
fi
# shellcheck disable=SC2154
if [[ -n "$AUTOMATION_LIB_PATH" ]]; then
        # shellcheck source=/usr/share/automation/lib/common_lib.sh
        source $AUTOMATION_LIB_PATH/common_lib.sh
else
    (
    echo "WARNING: It does not appear that containers/automation was installed."
    echo "         Functionality of most of this library will be negatively impacted"
    echo "         This ${BASH_SOURCE[0]} was loaded by ${BASH_SOURCE[1]}"
    ) > /dev/stderr
fi

# Managed by setup.sh; holds task-specific definitions.
if [[ -r "/etc/ci_environment" ]]; then source /etc/ci_environment; fi

OS_RELEASE_ID="$(source /etc/os-release; echo $ID)"
# GCE image-name compatible string representation of distribution _major_ version
OS_RELEASE_VER="$(source /etc/os-release; echo $VERSION_ID | tr -d '.')"
# Combined to ease soe usage
OS_REL_VER="${OS_RELEASE_ID}-${OS_RELEASE_VER}"

# Essential default paths, many are overriden when executing under Cirrus-CI
# others are duplicated here, to assist in debugging.
GOPATH="${GOPATH:-/var/tmp/go}"
if type -P go &> /dev/null
then
    # required for go 1.12+
    export GOCACHE="${GOCACHE:-$HOME/.cache/go-build}"
    eval "$(go env)"
    # required by make and other tools
    export $(go env | cut -d '=' -f 1)
    # Ensure compiled tooling is reachable
    export PATH="$PATH:$GOPATH/bin"
fi
PATH="$HOME/bin:$GOPATH/bin:/usr/local/bin:$PATH"
CIRRUS_WORKING_DIR=${CIRRUS_WORKING_DIR:-/tmp/udica}
SCRIPT_BASE=${CIRRUS_WORKING_DIR}/.cirrus

CI="${CI:-false}"
CIRRUS_CI="${CIRRUS_CI:-false}"
CONTINUOUS_INTEGRATION="${CONTINUOUS_INTEGRATION:-false}"
CIRRUS_REPO_NAME=${CIRRUS_REPO_NAME:-udica}

# Unsafe env. vars for display
SECRET_ENV_RE='(IRCID)|(ACCOUNT)|(^GC[EP]..+)|(SSH)'

# END Global export of all variables
set +a

# Remove all files (except conmon, and the cni-config) provided by the distro version.
remove_packaged_podman_files() {
    echo "Removing packaged podman files to prevent conflicts with source build and testing."
    req_env_vars OS_RELEASE_ID
    if [[ "$OS_RELEASE_ID" =~ "ubuntu" ]]
    then
        LISTING_CMD="sudo -E dpkg-query -L podman"
    else
        LISTING_CMD='sudo rpm -ql podman'
    fi

    # yum/dnf/dpkg may list system directories, only remove files
    $LISTING_CMD | while read fullpath
    do
        # TODO: This can go away when conmon gets it's own package
        if [[ -d "$fullpath" ]] || [[ $(basename "$fullpath") == "conmon" ]] || \
            [[ $(dirname "$fullpath") == "/etc/cni/net.d" ]]; then continue; fi
        ooe.sh sudo rm -vf "$fullpath"
    done
}
