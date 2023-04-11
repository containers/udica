# Copyright (C) 2018 Lukas Vrabec, <lvrabec@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from shutil import copy
from os import chdir, getcwd, remove
from os.path import exists
import tarfile

import selinux
import semanage

import udica.perms as perms

# Check if templates are present in current directory
# if yes, the templates directory is used instead of system one.
TEMPLATES_STORE = (
    "./templates" if exists("./templates") else "/usr/share/udica/templates"
)

CONFIG_CONTAINER = "/etc"
HOME_CONTAINER = "/home"
LOG_CONTAINER = "/var/log"
TMP_CONTAINER = "/tmp"

TEMPLATE_PLAYBOOK = "/usr/share/udica/ansible/deploy-module.yml"
VARIABLE_FILE_NAME = "variables-deploy-module.yml"

templates_to_load = []


def add_template(template):
    templates_to_load.append(template)


def list_templates_to_string(templates_to_load):
    return ".cil,".join(map(str, templates_to_load)) + ".cil"


def list_contexts(directory):
    directory_len = len(directory)

    handle = semanage.semanage_handle_create()
    semanage.semanage_connect(handle)

    (rc, fclist) = semanage.semanage_fcontext_list(handle)
    (rc, fclocal) = semanage.semanage_fcontext_list_local(handle)
    (rc, fchome) = semanage.semanage_fcontext_list_homedirs(handle)

    contexts = []
    for fcontext in fclist + fclocal + fchome:
        expression = semanage.semanage_fcontext_get_expr(fcontext)
        if expression[0:directory_len] == directory:
            context = semanage.semanage_fcontext_get_con(fcontext)
            if context:
                contexts.append(semanage.semanage_context_get_type(context))

    selabel = selinux.selabel_open(selinux.SELABEL_CTX_FILE, None, 0)
    try:
        (rc, context) = selinux.selabel_lookup(selabel, directory, 0)
    except FileNotFoundError:
        # File context definition containing "<<none>>" triggers exception
        context = None
    if context:
        contexts.append(context.split(":")[2])

    # Get the real label (ls -lZ) - may differ from what selabel_lookup returns
    try:
        context = selinux.getfilecon(directory)[1]
    except FileNotFoundError:
        context = None

    if context:
        contexts.append(context.split(":")[2])

    return contexts


def list_ports(port_number, port_proto):
    handle = semanage.semanage_handle_create()
    semanage.semanage_connect(handle)

    (rc, plist) = semanage.semanage_port_list(handle)
    (rc, plocal) = semanage.semanage_port_list_local(handle)

    for port in plocal + plist:
        con = semanage.semanage_port_get_con(port)
        ctype = semanage.semanage_context_get_type(con)
        proto = semanage.semanage_port_get_proto(port)
        proto_str = semanage.semanage_port_get_proto_str(proto)
        low = semanage.semanage_port_get_low(port)
        high = semanage.semanage_port_get_high(port)
        if low <= port_number <= high and port_proto == proto_str:
            return ctype


def create_policy(
    opts, capabilities, devices, mounts, ports, append_rules, inspect_format
):
    policy = open(opts["ContainerName"] + ".cil", "w")
    policy.write("(block " + opts["ContainerName"] + "\n")
    policy.write("    (blockinherit container)\n")
    add_template("base_container")

    if opts["FullNetworkAccess"]:
        policy.write("    (blockinherit net_container)\n")
        add_template("net_container")

    if opts["VirtAccess"]:
        policy.write("    (blockinherit virt_container)\n")
        add_template("virt_container")

    if opts["XAccess"]:
        policy.write("    (blockinherit x_container)\n")
        add_template("x_container")

    if opts["TtyAccess"]:
        policy.write("    (blockinherit tty_container)\n")
        add_template("tty_container")

    if ports:
        policy.write("    (blockinherit restricted_net_container)\n")
        add_template("net_container")

    if opts["StreamConnect"]:
        policy.write(
            "    (allow process "
            + opts["StreamConnect"]
            + ".process ( unix_stream_socket ( connectto ))) \n"
        )
        policy.write(
            "    (allow process "
            + opts["StreamConnect"]
            + ".socket ( sock_file ( getattr write open append ))) \n"
        )

    # capabilities
    if capabilities:
        caps = ""
        for item in capabilities:
            # Capabilities parsed from podman inspection JSON file have prefix "CAP_", this should be removed
            if "CAP_" in item:
                caps = caps + item[4:].lower() + " "
            else:
                caps = caps + item.lower() + " "

        policy.write("    (allow process process ( capability ( " + caps + "))) \n")
        policy.write("\n")

    # ports
    for item in sorted(ports, key=lambda x: x.get("portNumber", 0)):
        if "portNumber" in item:
            policy.write(
                "    (allow process "
                + list_ports(item["portNumber"], item["protocol"])
                + " ( "
                + perms.socket[item["protocol"]]
                + " (  name_bind ))) \n"
            )

    # devices
    # Not applicable for CRI-O container engine
    if inspect_format != "CRI-0":
        if opts["Devices"]:
            devices = [{"PathOnHost": device} for device in opts["Devices"].split(",")]
        write_policy_for_podman_devices(devices, policy)

    # mounts
    if inspect_format == "CRI-O":
        write_policy_for_crio_mounts(mounts, policy)
    elif inspect_format == "containerd":
        write_policy_for_containerd_mounts(mounts, policy)
    else:
        write_policy_for_podman_mounts(mounts, policy)

    if append_rules != None:
        for rule in append_rules:
            if opts["ContainerName"] in rule[0]:
                policy.write(
                    "    (allow process "
                    + rule[1]
                    + " ( "
                    + rule[2]
                    + " ( "
                    + rule[3]
                    + " ))) \n"
                )
            else:
                print(
                    "WARNING: process type: "
                    + rule[0]
                    + " seems to be unrelated to this container policy. Skipping allow rule."
                )

    policy.write(")")
    policy.close()


def write_policy_for_crio_mounts(mounts, policy):
    contexts = []
    contexts_readonly = []

    for item in mounts:
        if item["hostPath"].startswith("/var/lib/kubelet"):
            # These should already have the right context
            continue
        if item["hostPath"] == LOG_CONTAINER:
            if item["readonly"]:
                policy.write("    (blockinherit log_container)\n")
            else:
                policy.write("    (blockinherit log_rw_container)\n")
            add_template("log_container")
            continue

        if item["hostPath"] == HOME_CONTAINER:
            if item["readonly"]:
                policy.write("    (blockinherit home_container)\n")
            else:
                policy.write("    (blockinherit home_rw_container)\n")
            add_template("home_container")
            continue

        if item["hostPath"] == TMP_CONTAINER:
            if item["readonly"]:
                policy.write("    (blockinherit tmp_container)\n")
            else:
                policy.write("    (blockinherit tmp_rw_container)\n")
            add_template("tmp_container")
            continue

        if item["hostPath"] == CONFIG_CONTAINER:
            if item["readonly"]:
                policy.write("    (blockinherit config_container)\n")
            else:
                policy.write("    (blockinherit config_rw_container)\n")
            add_template("config_container")
            continue

        # TODO(jaosorior): Add prefix-dir to path. This way we could call this
        # from a container in kubernetes
        if item["readonly"] is False:
            contexts.extend(list_contexts(item["hostPath"]))
        else:
            contexts_readonly.extend(list_contexts(item["hostPath"]))

    for context in sorted(set(contexts)):
        policy.write(
            "    (allow process "
            + context
            + " ( dir ( "
            + perms.perm["dir_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( file ( "
            + perms.perm["file_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( fifo_file ( "
            + perms.perm["fifo_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( sock_file ( "
            + perms.perm["socket_rw"]
            + " ))) \n"
        )

    for context in sorted(set(contexts_readonly)):
        policy.write(
            "    (allow process "
            + context
            + " ( dir ( "
            + perms.perm["dir_ro"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( file ( "
            + perms.perm["file_ro"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( fifo_file ( "
            + perms.perm["fifo_ro"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( sock_file ( "
            + perms.perm["socket_ro"]
            + " ))) \n"
        )


def write_policy_for_podman_devices(devices, policy):
    contexts = []

    for item in devices:
        contexts.extend(list_contexts(item["PathOnHost"]))

    for context in sorted(set(contexts)):
        policy.write(
            "    (allow process "
            + context
            + " ( blk_file ( "
            + perms.perm["device_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( chr_file ( "
            + perms.perm["device_rw"]
            + " ))) \n"
        )


def write_policy_for_podman_mounts(mounts, policy):
    contexts = []
    contexts_rw = []

    for item in mounts:
        if not item["Source"].find("/"):
            if item["Source"] == LOG_CONTAINER and item["RW"] is False:
                policy.write("    (blockinherit log_container)\n")
                add_template("log_container")
                continue

            if item["Source"] == LOG_CONTAINER and item["RW"] is True:
                policy.write("    (blockinherit log_rw_container)\n")
                add_template("log_container")
                continue

            if item["Source"] == HOME_CONTAINER and item["RW"] is False:
                policy.write("    (blockinherit home_container)\n")
                add_template("home_container")
                continue

            if item["Source"] == HOME_CONTAINER and item["RW"] is True:
                policy.write("    (blockinherit home_rw_container)\n")
                add_template("home_container")
                continue

            if item["Source"] == TMP_CONTAINER and item["RW"] is False:
                policy.write("    (blockinherit tmp_container)\n")
                add_template("tmp_container")
                continue

            if item["Source"] == TMP_CONTAINER and item["RW"] is True:
                policy.write("    (blockinherit tmp_rw_container)\n")
                add_template("tmp_container")
                continue

            if item["Source"] == CONFIG_CONTAINER and item["RW"] is False:
                policy.write("    (blockinherit config_container)\n")
                add_template("config_container")
                continue

            if item["Source"] == CONFIG_CONTAINER and item["RW"] is True:
                policy.write("    (blockinherit config_rw_container)\n")
                add_template("config_container")
                continue

            if item["RW"] is True:
                contexts_rw.extend(list_contexts(item["Source"]))
            else:
                contexts.extend(list_contexts(item["Source"]))

    for context in sorted(set(contexts_rw)):
        policy.write(
            "    (allow process "
            + context
            + " ( dir ( "
            + perms.perm["dir_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( file ( "
            + perms.perm["file_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( fifo_file ( "
            + perms.perm["fifo_rw"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( sock_file ( "
            + perms.perm["socket_rw"]
            + " ))) \n"
        )

    for context in sorted(set(contexts)):
        policy.write(
            "    (allow process "
            + context
            + " ( dir ( "
            + perms.perm["dir_ro"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( file ( "
            + perms.perm["file_ro"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( fifo_file ( "
            + perms.perm["fifo_ro"]
            + " ))) \n"
        )
        policy.write(
            "    (allow process "
            + context
            + " ( sock_file ( "
            + perms.perm["socket_ro"]
            + " ))) \n"
        )


def write_policy_for_containerd_mounts(mounts, policy):
    # mount JSON example:
    # {
    #   "destination": "/sys/fs/cgroup",
    #   "type": "cgroup",
    #   "source": "cgroup",
    #   "options": [
    #     "ro",
    #     "nosuid",
    #     "noexec",
    #     "nodev"
    #     ]
    # }
    for item in sorted(mounts, key=lambda x: str(x["source"])):
        if not item["source"].find("/"):
            if item["source"] == LOG_CONTAINER and "ro" in item["options"]:
                policy.write("    (blockinherit log_container)\n")
                add_template("log_container")
                continue

            if item["source"] == LOG_CONTAINER and "ro" not in item["options"]:
                policy.write("    (blockinherit log_rw_container)\n")
                add_template("log_container")
                continue

            if item["source"] == HOME_CONTAINER and "ro" in item["options"]:
                policy.write("    (blockinherit home_container)\n")
                add_template("home_container")
                continue

            if item["source"] == HOME_CONTAINER and "ro" not in item["options"]:
                policy.write("    (blockinherit home_rw_container)\n")
                add_template("home_container")
                continue

            if item["source"] == TMP_CONTAINER and "ro" in item["options"]:
                policy.write("    (blockinherit tmp_container)\n")
                add_template("tmp_container")
                continue

            if item["source"] == TMP_CONTAINER and "ro" not in item["options"]:
                policy.write("    (blockinherit tmp_rw_container)\n")
                add_template("tmp_container")
                continue

            if item["source"] == CONFIG_CONTAINER and "ro" in item["options"]:
                policy.write("    (blockinherit config_container)\n")
                add_template("config_container")
                continue

            if item["source"] == CONFIG_CONTAINER and "ro" not in item["options"]:
                policy.write("    (blockinherit config_rw_container)\n")
                add_template("config_container")
                continue

            contexts = list_contexts(item["source"])
            for context in contexts:
                if "ro" not in item["options"]:
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( dir ( "
                        + perms.perm["dir_rw"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( file ( "
                        + perms.perm["file_rw"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( fifo_file ( "
                        + perms.perm["fifo_rw"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( sock_file ( "
                        + perms.perm["socket_rw"]
                        + " ))) \n"
                    )
                if "ro" in item["options"]:
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( dir ( "
                        + perms.perm["dir_ro"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( file ( "
                        + perms.perm["file_ro"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( fifo_file ( "
                        + perms.perm["fifo_ro"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( sock_file ( "
                        + perms.perm["socket_ro"]
                        + " ))) \n"
                    )


def load_policy(opts):
    PWD = getcwd()

    if not exists(TEMPLATES_STORE):
        print("Policy templates not found! Please install container-selinux package.")
        exit(1)

    chdir(TEMPLATES_STORE)

    if opts["LoadModules"]:
        handle = semanage.semanage_handle_create()
        semanage.semanage_connect(handle)

        for template in templates_to_load:
            semanage.semanage_module_install_file(handle, template + ".cil")

        chdir(PWD)

        semanage.semanage_module_install_file(handle, opts["ContainerName"] + ".cil")

        semanage.semanage_commit(handle)
    else:
        templates = list_templates_to_string(templates_to_load)
        if len(templates_to_load) > 1:
            print(
                "\nPlease load these modules using: \n# semodule -i "
                + opts["ContainerName"]
                + ".cil "
                + TEMPLATES_STORE
                + "/{"
                + templates
                + "}"
            )
        else:
            print(
                "\nPlease load these modules using: \n# semodule -i "
                + opts["ContainerName"]
                + ".cil "
                + TEMPLATES_STORE
                + "/"
                + templates
                + ""
            )

        chdir(PWD)


def generate_playbook(opts):
    src = TEMPLATE_PLAYBOOK
    dst = "./"
    copy(src, dst)

    with open(VARIABLE_FILE_NAME, "w") as varsfile:
        varsfile.write("archive: " + opts["ContainerName"] + "-policy.tar.gz\n")
        varsfile.write(
            "policy: "
            + opts["ContainerName"]
            + ".cil "
            + list_templates_to_string(templates_to_load).replace(",", " ")
            + "\n"
        )
        varsfile.write("final_policy: " + opts["ContainerName"] + ".cil")

    with tarfile.open(opts["ContainerName"] + "-policy.tar.gz", "w:gz") as tar:
        for template in templates_to_load:
            tar.add(TEMPLATES_STORE + "/" + template + ".cil", template + ".cil")
        tar.add(opts["ContainerName"] + ".cil")
        remove(opts["ContainerName"] + ".cil")

    print(
        "\nAnsible playbook and archive with udica policies generated! \n"
        + "Please run ansible play to deploy the policy."
    )
