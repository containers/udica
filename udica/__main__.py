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

import argparse
import subprocess
import sys

# import udica
from udica.parse import parse_avc_file
from udica.parse import ENGINE_ALL, ENGINE_PODMAN, ENGINE_DOCKER
from udica.version import version
from udica import parse
from udica.policy import create_policy, load_policy, generate_playbook


def get_args():
    if "confined_user" in sys.argv:
        # set up confined_user parser (do not show normal "udica" options)
        parser = argparse.ArgumentParser(
            description="SELinux confined user policy generator"
        )
        parser.add_argument("confined_user")
        parser.add_argument(
            "-a",
            "--admin_commands",
            action="store_true",
            default=False,
            dest="admin_commands",
            help="Use administrative commands (vipw, passwd, ...)",
        )
        parser.add_argument(
            "-g",
            "--graphical_login",
            action="store_true",
            default=False,
            dest="graphical_login",
            help="Use graphical login environment",
        )
        parser.add_argument(
            "-m",
            "--mozilla_usage",
            action="store_true",
            default=False,
            dest="mozilla_usage",
            help="Use mozilla firefox",
        )
        parser.add_argument(
            "-n",
            "--networking",
            action="store_true",
            default=False,
            dest="networking",
            help="Manage basic networking (ip, ifconfig, traceroute, tcpdump, ...)",
        )
        parser.add_argument(
            "-d",
            "--security_advanced",
            action="store_true",
            default=False,
            dest="security_advanced",
            help="Manage SELinux settings (semanage, semodule, sepolicy, ...)",
        )
        parser.add_argument(
            "-i",
            "--security_basic",
            action="store_true",
            default=False,
            dest="security_basic",
            help="Use read-only security-related tools (seinfo, getsebool, sesearch, ...)",
        )
        parser.add_argument(
            "-s",
            "--sudo",
            action="store_true",
            default=False,
            dest="sudo",
            help="Run commands as root using sudo",
        )
        parser.add_argument(
            "-l",
            "--user_login",
            action="store_true",
            default=True,
            dest="user_login",
            help="Basic rules common to all users (tty, pty, ...)",
        )
        parser.add_argument(
            "-c",
            "--ssh_connect",
            action="store_true",
            default=False,
            dest="ssh_connect",
            help="Connect over SSH",
        )
        parser.add_argument(
            "-b",
            "--basic_commands",
            action="store_true",
            default=False,
            dest="basic_commands",
            help="Use basic commands (date, ls, ps, man, systemctl -user, journalctl -user, passwd, ...)",
        )
        parser.add_argument(
            "--level",
            nargs="?",
            default="s0",
            dest="level",
            help='MLS/MCS level, defaults to "s0"',
        )
        parser.add_argument(
            "--range",
            nargs="?",
            default="s0-s0:c0.c1023",
            dest="range",
            help='MLS/MCS range, defaults to "s0-s0:c0.c1023"',
        )
        parser.add_argument("uname")
    else:
        # set up normal udica parser
        parser = argparse.ArgumentParser(
            description="Script generates SELinux policy for running container.",
            prog="udica [confined_user]",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""Additional options:
  confined_user		Generate policy for a new confined user instead of a container policy""",
        )
        parser.add_argument("-V", "--version", action="version", version=version)
        parser.add_argument(
            type=str, help="Name for SELinux policy module", dest="ContainerName"
        )
        parser.add_argument(
            "-i",
            "--container-id",
            type=str,
            help="Running container ID",
            dest="ContainerID",
            default=None,
        )
        parser.add_argument(
            "-j",
            "--json",
            help='Load json from this file, use "-j -" for stdin',
            required=False,
            dest="JsonFile",
            default=None,
        )
        parser.add_argument(
            "--full-network-access",
            help="Allow container full Network access ",
            required=False,
            dest="FullNetworkAccess",
            action="store_true",
        )
        parser.add_argument(
            "--tty-access",
            help="Allow container to read and write the controlling terminal ",
            required=False,
            dest="TtyAccess",
            action="store_true",
        )
        parser.add_argument(
            "--X-access",
            help="Allow container to communicate with Xserver ",
            required=False,
            dest="XAccess",
            action="store_true",
        )
        parser.add_argument(
            "--virt-access",
            help="Allow container to communicate with libvirt ",
            required=False,
            dest="VirtAccess",
            action="store_true",
        )
        parser.add_argument(
            "-s",
            "--stream-connect",
            help="Allow container to stream connect with given SELinux domain ",
            required=False,
            dest="StreamConnect",
        )
        parser.add_argument(
            "-l",
            "--load-modules",
            help="Load templates and module created by this tool ",
            required=False,
            dest="LoadModules",
            action="store_true",
        )
        parser.add_argument(
            "-c",
            "--caps",
            help='List of capabilities, e.g "-c AUDIT_WRITE,CHOWN,DAC_OVERRIDE,FOWNER,FSETID,KILL,MKNOD,NET_BIND_SERVICE,NET_RAW,SETFCAP,SETGID,SETPCAP,SETUID,SYS_CHROOT"',
            required=False,
            dest="Caps",
            default=None,
        )
        parser.add_argument(
            "--devices",
            type=str,
            help='List of devices the container should have access to, e.g "--devices /dev/dri/card0,/dev/dri/renderD128"',
            dest="Devices",
            required=False,
            default=None,
        )
        parser.add_argument(
            "-d",
            "--ansible",
            help="Generate ansible playbook to deploy SELinux policy for containers ",
            required=False,
            dest="Ansible",
            action="store_true",
        )
        parser.add_argument(
            "-a",
            "--append-rules",
            type=str,
            help="Append more SELinux allow rules from file",
            dest="FileAVCS",
            required=False,
            default=None,
        )
        parser.add_argument(
            "-e",
            "--container-engine",
            type=str,
            help="Specify which container engine is used for the inspected container (supports: {})".format(
                ", ".join(ENGINE_ALL)
            ),
            dest="ContainerEngine",
            required=False,
            default="-",
        )

    args = parser.parse_args()
    return vars(args)


def main():
    opts = get_args()

    # generate confined user policy
    if "confined_user" in opts.keys():
        from udica.confined_user import create_confined_user_policy

        create_confined_user_policy(opts)
        return

    if opts["ContainerID"]:
        container_inspect_raw = None
        for backend in [ENGINE_PODMAN, ENGINE_DOCKER]:
            try:
                run_inspect = subprocess.Popen(
                    [backend, "inspect", opts["ContainerID"]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                inspect_data = run_inspect.communicate()[0]
                if run_inspect.returncode != 0:
                    inspect_data = None
            except FileNotFoundError:
                inspect_data = None

            if inspect_data:
                container_inspect_raw = inspect_data
                break

        if not container_inspect_raw:
            print("Container with specified ID does not exits!")
            exit(3)

    if opts["JsonFile"]:
        if opts["JsonFile"] == "-":
            container_inspect_raw = sys.stdin.read()
        else:
            import os.path

            if os.path.isfile(opts["JsonFile"]):
                with open(opts["JsonFile"], "r") as f:
                    container_inspect_raw = f.read()
            else:
                print("Json file does not exists!")
                exit(3)

    if (not opts["JsonFile"]) and (not opts["ContainerID"]):
        try:
            container_inspect_raw = sys.stdin.read()
        except Exception as e:
            print("Couldn't parse inspect data from stdin:", e)
            exit(3)

    try:
        engine_helper = parse.get_engine_helper(
            container_inspect_raw, opts["ContainerEngine"]
        )
    except Exception as e:
        print("Couldn't parse inspect data:", e)
        exit(3)
    container_inspect = engine_helper.parse_inspect(container_inspect_raw)
    container_devices = engine_helper.get_devices(container_inspect)
    container_mounts = engine_helper.get_mounts(container_inspect)
    container_ports = engine_helper.get_ports(container_inspect)

    # Append allow rules if AVCs log is provided
    append_rules = None
    if opts["FileAVCS"]:
        import os.path

        if os.path.isfile(opts["FileAVCS"]):
            with open(opts["FileAVCS"], "r") as f:
                try:
                    append_rules = parse_avc_file(f.read())
                except Exception as e:
                    print("Couldn't parse AVC file:", e)
                    exit(3)
            f.close()
        else:
            print("AVC file does not exists!")
            exit(3)

    container_caps = []

    container_caps = sorted(engine_helper.get_caps(container_inspect, opts))

    try:
        create_policy(
            opts,
            container_caps,
            container_devices,
            container_mounts,
            container_ports,
            append_rules,
            engine_helper.container_engine,
        )
    except Exception as e:
        print("Couldn't create policy:", e)
        exit(4)

    print("\nPolicy " + opts["ContainerName"] + " created!")

    if opts["Ansible"]:
        generate_playbook(opts)
    else:
        load_policy(opts)

    print(
        '\nRestart the container with: "--security-opt label=type:'
        + opts["ContainerName"]
        + '.process" parameter'
    )


if __name__ == "__main__":
    main()
