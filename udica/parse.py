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

import json

#: Constant for the podman engine
ENGINE_PODMAN = "podman"

#: Constant for the cri-o engine
ENGINE_CRIO = "CRI-O"

#: Constant for the docker engine
ENGINE_DOCKER = "docker"

#: All supported engines
ENGINE_ALL = [ENGINE_PODMAN, ENGINE_CRIO, ENGINE_DOCKER]


def json_is_podman_or_docker_format(json_rep):
    """Check if the inspected file is in a format from docker or podman.

    We know this because the type in the inspect command will be a list
    """
    return isinstance(json_rep, list)


def json_is_podman_format(json_rep):
    """Check if the inspected file is in a format from podman. """
    return isinstance(json_rep, list) and (
        "container=oci" in json_rep[0]["Config"]["Env"]
        or "container=podman" in json_rep[0]["Config"]["Env"]
    )


def adjust_json_from_docker(json_rep):
    """If the json comes from a docker call, we need to adjust it to make use
    of it. """

    if not isinstance(json_rep[0]["NetworkSettings"]["Ports"], dict):
        raise Exception(
            "Error parsing docker engine inspection JSON structure, try to specify container engine using '--container-engine' parameter"
        )

    for item in json_rep[0]["Mounts"]:
        item["source"] = item["Source"]
        if item["Mode"] == "rw":
            item["options"] = "rw"
        if item["Mode"] == "ro":
            item["options"] = "ro"


def parse_inspect(data, ContainerEngine):
    json_rep = json.loads(data)
    engine = validate_container_engine(ContainerEngine)
    if engine == "-":
        if json_is_podman_or_docker_format(json_rep):
            if not json_is_podman_format(json_rep):
                adjust_json_from_docker(json_rep)

    if engine == ENGINE_DOCKER:
        adjust_json_from_docker(json_rep)

    return json_rep


def get_inspect_format(data, ContainerEngine):
    engine = validate_container_engine(ContainerEngine)
    if engine == "-":
        json_rep = json.loads(data)
        if json_is_podman_or_docker_format(json_rep):
            if json_is_podman_format(json_rep):
                return ENGINE_PODMAN
            return ENGINE_DOCKER
        return ENGINE_CRIO
    else:
        return engine


def get_mounts(data, inspect_format):
    if inspect_format in [ENGINE_PODMAN, ENGINE_DOCKER]:
        return data[0]["Mounts"]
    if inspect_format == ENGINE_CRIO and not json_is_podman_or_docker_format(data):
        return data["status"]["mounts"]
    raise Exception("Error getting mounts from unknown format %s" % inspect_format)


def get_ports(data, inspect_format):
    if inspect_format in [ENGINE_PODMAN, ENGINE_DOCKER]:
        ports = []
        for key, value in data[0]["NetworkSettings"]["Ports"].items():
            container_port = str(key).split("/")
            host_port = value[0]["HostPort"]
            new_port = {"hostPort": int(host_port), "protocol": container_port[1]}
            ports.append(new_port)
        return ports

    if inspect_format == ENGINE_CRIO:
        # Not applicable in the CRI-O case, since this is handled by the
        # kube-proxy/CNI.
        return []
    raise Exception("Error getting ports from unknown format %s" % inspect_format)


def get_caps(data, opts, inspect_format):
    if opts["Caps"]:
        if opts["Caps"] == "None":
            return []
        return opts["Caps"].split(",")

    if inspect_format == ENGINE_PODMAN:
        return data[0]["EffectiveCaps"]
    return []


def parse_cap(data):
    return data.decode().split("\n")[1].split(",")


def context_to_type(context):
    return context.split("=")[1].split(":")[2]


def remove_dupe_perms(string):
    perms = string.split()
    return " ".join(sorted(set(perms), key=perms.index))


def parse_avc_file(data):
    append_rules = []

    for avc in data.splitlines():
        new_rule = []
        items = avc.split(" ")

        if "type=AVC" not in items[0]:
            continue

        for item in items:
            if "scontext" in item:
                new_rule.append(context_to_type(item))
            if "tcontext" in item:
                new_rule.append(context_to_type(item))
            if "tclass" in item:
                new_rule.append(item.split("=")[1])

        open_bracket = items.index("{")
        perm = open_bracket + 1
        new_rule.append(items[perm])

        for rule in append_rules:
            if (
                rule[0] == new_rule[0]
                and rule[1] == new_rule[1]
                and rule[2] == new_rule[2]
            ):
                new_rule[3] = rule[3] + " " + new_rule[3]
                append_rules.remove(rule)
        new_rule[3] = remove_dupe_perms(new_rule[3])
        append_rules.append(new_rule)

    return append_rules


def validate_container_engine(ContainerEngine):
    if ContainerEngine in ENGINE_ALL + ["CRIO", "-"]:
        # Fix CRIO reference to use ENGINE_CRIO
        if ContainerEngine == "CRIO":
            return ENGINE_CRIO
        return ContainerEngine
    else:
        raise Exception("Container Engine %s is not supported." % ContainerEngine)
