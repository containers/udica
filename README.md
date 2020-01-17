![UDICA logo](logo/logo-udica.svg)

# udica - Generate SELinux policies for containers!

<a href="https://copr.fedorainfracloud.org/coprs/lvrabec/udica/package/udica/"><img src="https://copr.fedorainfracloud.org/coprs/lvrabec/udica/package/udica/status_image/last_build.png" /></a>
[![Build Status](https://travis-ci.org/containers/udica.svg?branch=master)](https://travis-ci.org/containers/udica)

# Overview

This repository contains a tool for generating SELinux security profiles for containers. The whole concept is based on "block inheritence" feature inside CIL intermediate language supported by SELinux userspace. The tool creates a policy which combines rules inherited from specified CIL blocks(templates) and rules discovered by inspection of container JSON file, which contains mountpoints and ports definitions.

Final policy could be loaded immediately or moved to another system where it could be loaded via semodule.

## What's with the weird name?
The name of this tool is derived from the Slovak word "udica" *\[uɟit͡sa\]*, which means "fishing rod". It is a reference to the saying *"Give a man a fish and you feed him for a day; teach a man to fish and you feed him for a lifetime."* Here udica is the fishing rod that allows you to get the fish (container policy) yourself, instead of always having to ask your local fisherman (SELinux expert) to catch (create) it for you ;)

## State

This tool is still in early phase of development. Any feedback, ideas, pull requests are welcome. We're still adding new features, parameters and policy blocks which could be used.

## Proof of concept

Tool was created based on following PoC where process of creating policy is described:
https://github.com/fedora-selinux/container-selinux-customization

## Supported container engines

Udica supports following container engines:
   * CRI-O v1.14.10+
   * docker v1.13+
   * podman v1.4+

## Installing

Install udica tool with all dependencies

    $ sudo dnf install -y podman setools-console git container-selinux
    $ git clone https://github.com/containers/udica
    $ cd udica && sudo python3 ./setup.py install

Alternatively you can run udica directly from git:

    $ python3 -m udica --help

Another way how to install udica is to use fedora repository:

    # dnf install udica -y

Or you can use Python Package Index (Pypi):

    # pip install udica

Make sure that SELinux is in Enforcing mode

    # setenforce 1
    # getenforce
    Enforcing

## Current situation

Let's start podman container with following parameters:

    # podman run -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 -it fedora bash

 - Container will bind mount /home with read only perms
 - Container will bind mount /var/spool with read/write perms
 - Container will publish container's port 21 to the host

Container runs with **container\_t** type and **c447,c628** categories.

Access mounted */home* is not working:

    [root@37a3635afb8f /]# cd /home/
    [root@37a3635afb8f home]# ls
    ls: cannot open directory '.': Permission denied

Because there is no allow rule for **container\_t** to access */home*

    # sesearch -A -s container_t -t home_root_t
    #

Access mounted */var/spool* is not working:

    [root@37a3635afb8f home]# cd /var/spool/
    [root@37a3635afb8f spool]# ls
    ls: cannot open directory '.': Permission denied
    [root@37a3635afb8f spool]# touch test
    touch: cannot touch 'test': Permission denied

Because there is no allow rule for **container\_t** to access */var/spool*

    # sesearch -A -s container_t -t var_spool_t -c dir -p read
    #

On the other hand, what is completely allowed is network access.

    # sesearch -A -s container_t -t port_type -c tcp_socket
    allow container_net_domain port_type:tcp_socket { name_bind name_connect recv_msg send_msg };
    allow sandbox_net_domain port_type:tcp_socket { name_bind name_connect recv_msg send_msg };

    # sesearch -A -s container_t -t port_type -c udp_socket
    allow container_net_domain port_type:udp_socket { name_bind recv_msg send_msg };
    allow sandbox_net_domain port_type:udp_socket { name_bind recv_msg send_msg };

It would be great to restrict this access and allow container bind just on tcp port *21* or with the same label.

## Creating SELinux policy for container

To create policy for container, it's necessary to have running container for which a policy will be generated. Container from previous chapter will be used.

Let's find container id using *podman ps* command:

    # podman ps
    CONTAINER ID   IMAGE                             COMMAND   CREATED          STATUS              PORTS   NAMES
    37a3635afb8f   docker.io/library/fedora:latest   bash      15 minutes ago   Up 15 minutes ago           heuristic_lewin

Container ID is **37a3635afb8f**.

To create policy for it **udica** tool could be used. Parameter '*-j*' is for *container json file* and SELinux policy *name* for container.

    # podman inspect 37a3635afb8f > container.json
    # udica -j container.json  my_container

or

    # podman inspect 37a3635afb8f | udica  my_container

    Policy my_container with container id 37a3635afb8f created!

    Please load these modules using:
    # semodule -i my_container.cil /usr/share/udica/templates/{base_container.cil,net_container.cil,home_container.cil}

    Restart the container with: "--security-opt label=type:my_container.process" parameter

Policy is generated. Let's follow instructions from output:

    # semodule -i my_container.cil /usr/share/udica/templates/{base_container.cil,net_container.cil,home_container.cil}

    # podman run --security-opt label=type:my_container.process -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 -it fedora bash

Container is now running with **my\_container.process** type:

    # ps -efZ | grep my_container.process
    unconfined_u:system_r:container_runtime_t:s0-s0:c0.c1023 root 2275 434  1 13:49 pts/1 00:00:00 podman run --security-opt label=type:my_container.process -v /home:/home:ro -v /var/spool:/var/spool:rw -p 21:21 -it fedora bash
    system_u:system_r:my_container.process:s0:c270,c963 root 2317 2305  0 13:49 pts/0 00:00:00 bash

Proof that SELinux now allowing access */home* and */var/spool* mount points:

    [root@814ec56079e5 /]# cd /home
    [root@814ec56079e5 home]# ls
    lvrabec

    [root@814ec56079e5 ~]# cd /var/spool/
    [root@814ec56079e5 spool]# touch test
    [root@814ec56079e5 spool]#

Proof that SELinux allows binding only to tcp/udp *21* port.

    [root@5bd8cb2ad911 /]# nc -lvp 21
    Ncat: Version 7.60 ( https://nmap.org/ncat )
    Ncat: Generating a temporary 1024-bit RSA key. Use --ssl-key and --ssl-cert to use a permanent one.
    Ncat: SHA-1 fingerprint: 6EEC 102E 6666 5F96 CC4F E5FA A1BE 4A5E 6C76 B6DC
    Ncat: Listening on :::21
    Ncat: Listening on 0.0.0.0:21

    [root@5bd8cb2ad911 /]# nc -lvp 80
    Ncat: Version 7.60 ( https://nmap.org/ncat )
    Ncat: Generating a temporary 1024-bit RSA key. Use --ssl-key and --ssl-cert to use a permanent one.
    Ncat: SHA-1 fingerprint: 6EEC 102E 6666 5F96 CC4F E5FA A1BE 4A5E 6C76 B6DC
    Ncat: bind to :::80: Permission denied. QUITTING.

## Running from a container

To build the udica container to your local registry, run the following command:

    $ make image

Once having the image built, it's possible to run udica from whithin a
container. The necessary directories to bind-mount are:

* `/sys/fs/selinux`
* `/etc/selinux/`
* `/var/lib/selinux/`

For reference, this would be a way to call the container via podman:

    podman run --user root --privileged -ti \
        -v /sys/fs/selinux:/sys/fs/selinux \
        -v /etc/selinux/:/etc/selinux/ \
        -v /var/lib/selinux/:/var/lib/selinux/ \
        --rm --name=udica udica

## Testing

Udica repository contains units tests for basic functionality of the tool. To run tests follow these commands:

    $ make test

On SELinux enabled systems you can run also (root access required):

    # python3 tests/test_integration.py

## Udica in OpenShift

Udica could run in OpenShift and generate SELinux policies for pods in the same instance.
[SELinux policy helper operator](https://github.com/JAORMX/selinux-policy-helper-operator) is a controller that listens to all pods in the system. It will attempt to generate a policy for pods when the pod is annotated with a specific tag "generate-selinux-policy" and the pod is in a running state. In order to generate the policy, it spawns a pod with the [selinux-k8s](https://github.com/JAORMX/selinux-k8s) tool which uses udica to generate the policy. It will spit out a configmap with the appropriate policy.

Real example is demonstrated in following demo.

### Demo

[![asciicast](https://asciinema.org/a/RnjsiiQYRDiLcB8hbhKiIJF5B.svg)](https://asciinema.org/a/RnjsiiQYRDiLcB8hbhKiIJF5B)

## Known issues

   * It's not possible to detect capabilities used by container in docker engine, therefore you *have to* use '-c' to specify capabilities for docker container manually.
   * It's not possible to generate custom local policy using "audit2allow -M" tool from AVCs where source context was generated by udica. For this purpose please use '--append-rules' option.
   * In some situations udica fails to identify which container engine is used, therefore "--container-engine" parameter has to be used to inform udica how JSON inspection file should be parsed.
