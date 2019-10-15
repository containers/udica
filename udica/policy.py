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
    (rc, context) = selinux.selabel_lookup(selabel, directory, 0)
    if context == None:
        if exists(directory) == False:
            exit(1)
        context = selinux.getfilecon(directory)[1]
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


def create_policy(opts, capabilities, mounts, ports, append_rules, inspect_format):
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
                caps = caps + perms.cap[item[4:]]
            else:
                caps = caps + perms.cap[item]

        policy.write("    (allow process process ( capability ( " + caps + "))) \n")
        policy.write("\n")

    # ports
    for item in ports:
        if "hostPort" in item:
            policy.write(
                "    (allow process "
                + list_ports(item["hostPort"], item["protocol"])
                + " ( "
                + perms.socket[item["protocol"]]
                + " (  name_bind ))) \n"
            )

    # mounts
    if inspect_format == "CRI-O":
        write_policy_for_crio_mounts(mounts, policy)
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
        contexts = list_contexts(item["hostPath"])
        for context in contexts:
            if item["readonly"] is False:
                policy.write(
                    "    (allow process "
                    + context
                    + " ( dir ( "
                    + perms.perm["drw"]
                    + " ))) \n"
                )
                policy.write(
                    "    (allow process "
                    + context
                    + " ( file ( "
                    + perms.perm["frw"]
                    + " ))) \n"
                )
                policy.write(
                    "    (allow process "
                    + context
                    + " ( sock_file ( "
                    + perms.perm["srw"]
                    + " ))) \n"
                )
            else:
                policy.write(
                    "    (allow process "
                    + context
                    + " ( dir ( "
                    + perms.perm["dro"]
                    + " ))) \n"
                )
                policy.write(
                    "    (allow process "
                    + context
                    + " ( file ( "
                    + perms.perm["fro"]
                    + " ))) \n"
                )
                policy.write(
                    "    (allow process "
                    + context
                    + " ( sock_file ( "
                    + perms.perm["sro"]
                    + " ))) \n"
                )


def write_policy_for_podman_mounts(mounts, policy):
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

            contexts = list_contexts(item["Source"])
            for context in contexts:
                if item["RW"] is True:
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( dir ( "
                        + perms.perm["drw"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( file ( "
                        + perms.perm["frw"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( sock_file ( "
                        + perms.perm["srw"]
                        + " ))) \n"
                    )
                if item["RW"] is False:
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( dir ( "
                        + perms.perm["dro"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( file ( "
                        + perms.perm["fro"]
                        + " ))) \n"
                    )
                    policy.write(
                        "    (allow process "
                        + context
                        + " ( sock_file ( "
                        + perms.perm["sro"]
                        + " ))) \n"
                    )


def load_policy(opts):
    PWD = getcwd()
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
