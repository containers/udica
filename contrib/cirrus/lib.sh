

# Library of common, shared utility functions.  This file is intended
# to be sourced by other scripts, not called directly.

# Under some contexts these values are not set, make sure they are.
export USER="$(whoami)"
export HOME="$(getent passwd $USER | cut -d : -f 6)"
[[ -n "$UID" ]] || export UID=$(getent passwd $USER | cut -d : -f 3)
export GID=$(getent passwd $USER | cut -d : -f 4)

OS_RELEASE_ID="$(source /etc/os-release; echo $ID)"
# GCE image-name compatible string representation of distribution _major_ version
OS_RELEASE_VER="$(source /etc/os-release; echo $VERSION_ID | cut -d '.' -f 1)"
# Combined to ease soe usage
OS_REL_VER="${OS_RELEASE_ID}-${OS_RELEASE_VER}"

# Essential default paths, many are overriden when executing under Cirrus-CI
# others are duplicated here, to assist in debugging.
export GOPATH="${GOPATH:-/var/tmp/go}"
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
export PATH="$HOME/bin:$GOPATH/bin:/usr/local/bin:$PATH"
CIRRUS_WORKING_DIR=${CIRRUS_WORKING_DIR:-/tmp/udica}
SCRIPT_BASE=${CIRRUS_WORKING_DIR}/.cirrus

export CI="${CI:-false}"
CIRRUS_CI="${CIRRUS_CI:-false}"
CONTINUOUS_INTEGRATION="${CONTINUOUS_INTEGRATION:-false}"
CIRRUS_REPO_NAME=${CIRRUS_REPO_NAME:-udica}

# Unsafe env. vars for display
SECRET_ENV_RE='(IRCID)|(ACCOUNT)|(^GC[EP]..+)|(SSH)'

# Pass in a list of one or more envariable names; exit non-zero with
# helpful error message if any value is empty
req_env_var() {
    # Provide context. If invoked from function use its name; else script name
    local caller=${FUNCNAME[1]}
    if [[ -n "$caller" ]]; then
        # Indicate that it's a function name
        caller="$caller()"
    else
        # Not called from a function: use script name
        caller=$(basename $0)
    fi

    # Usage check
    [[ -n "$1" ]] || die 1 "FATAL: req_env_var: invoked without arguments"

    # Each input arg is an envariable name, e.g. HOME PATH etc. Expand each.
    # If any is empty, bail out and explain why.
    for i; do
        if [[ -z "${!i}" ]]; then
            die 9 "FATAL: $caller requires \$$i to be non-empty"
        fi
    done
}

show_env_vars() {
    echo "Showing selection of environment variable definitions:"
    _ENV_VAR_NAMES=$(awk 'BEGIN{for(v in ENVIRON) print v}' | \
        egrep -v "(^PATH$)|(^BASH_FUNC)|(^[[:punct:][:space:]]+)|$SECRET_ENV_RE" | \
        sort -u)
    for _env_var_name in $_ENV_VAR_NAMES
    do
        # Supports older BASH versions
        printf "    ${_env_var_name}=%q\n" "$(printenv $_env_var_name)"
    done
}

die() {
    echo "************************************************"
    echo ">>>>> ${2:-FATAL ERROR (but no message given!) in ${FUNCNAME[1]}()}"
    echo "************************************************"
    exit ${1:-1}
}

# It's like 'set -x' but only for one command at a time
showrun() {
    echo '--------------------------------------------------'
    echo '+ '$(printf " %q" "$@") > /dev/stderr
    "$@"
}

# Remove all files (except conmon, and the cni-config) provided by the distro version.
remove_packaged_podman_files() {
    echo "Removing packaged podman files to prevent conflicts with source build and testing."
    req_env_var OS_RELEASE_ID
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
