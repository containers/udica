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

import sys
import subprocess
import argparse

# import udica
from udica.parse import parse_inspect, parse_cap
from udica.policy import create_policy, load_policy

def get_args():
    parser = argparse.ArgumentParser(description='Script generates SELinux policy for running container.')
    parser.add_argument(
        type=str, help='Name for SELinux policy module', dest='ContainerName')
    parser.add_argument(
        '-i', '--container-id', type=str, help='Running container ID', dest='ContainerID', default=None)
    parser.add_argument(
        '-j', '--json', help='Load json from this file, use "-j -" for stdin', required=False, dest='JsonFile', default=None)
    parser.add_argument(
        '--full-network-access', help='Allow container full Network access ', required=False, dest='FullNetworkAccess', action='store_true')
    parser.add_argument(
        '--tty-access', help='Allow container to read and write the controlling terminal ', required=False, dest='TtyAccess', action='store_true')
    parser.add_argument(
        '--X-access', help='Allow container to communicate with Xserver ', required=False, dest='XAccess', action='store_true')
    parser.add_argument(
        '--virt-access', help='Allow container to communicate with libvirt ', required=False, dest='VirtAccess', action='store_true')
    parser.add_argument(
        '-l', '--load-modules', help='Load templates and module created by this tool ', required=False, dest='LoadModules', action='store_true')
    parser.add_argument(
        '-c', '--caps', help='List of capabilities, e.g "-c AUDIT_WRITE,CHOWN,DAC_OVERRIDE,FOWNER,FSETID,KILL,MKNOD,NET_BIND_SERVICE,NET_RAW,SETFCAP,SETGID,SETPCAP,SETUID,SYS_CHROOT"', required=False, dest='Caps', default=None)
    args = parser.parse_args()
    return vars(args)

def main():

    opts = get_args()

    if opts['ContainerID']:
        return_code_podman = subprocess.call(["podman", "inspect", opts['ContainerID']], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        return_code_docker = subprocess.call(["docker", "inspect", opts['ContainerID']], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        if ((return_code_podman != 0) and (return_code_docker != 0)):
            print('Container with specified ID does not exits!')
            exit(2)

        if (return_code_podman == 0):
            run_inspect = subprocess.Popen(["podman", "inspect", opts['ContainerID']], stdout=subprocess.PIPE)
            container_inspect_data = run_inspect.communicate()[0]

        if (return_code_docker == 0):
            run_inspect = subprocess.Popen(["docker", "inspect", opts['ContainerID']], stdout=subprocess.PIPE)
            container_inspect_data = run_inspect.communicate()[0]

    if opts['JsonFile']:
        if opts['JsonFile'] == '-':
            import sys
            container_inspect_data = sys.stdin.read()
        else:
            import os.path
            if os.path.isfile(opts['JsonFile']):
                with open(opts['JsonFile'], 'r') as f:
                    container_inspect_data = f.read()
            else:
                print('Json file does not exists!')
                exit(2)

    if (not opts['JsonFile']) and (not opts['ContainerID']):
        try:
            import sys
            container_inspect_data = sys.stdin.read()
        except:
            exit(2)

    if opts['Caps']:
        if opts['Caps'] == 'None':
            container_caps = []
        else:
            container_caps = opts['Caps'].split(',')
    else:
            container_caps = []

    container_inspect = parse_inspect(container_inspect_data)
    container_mounts = container_inspect[0]['Mounts']
    container_ports = container_inspect[0]['NetworkSettings']['Ports']

    create_policy(opts, container_caps, container_mounts, container_ports)

    print('\nPolicy ' + opts['ContainerName'] + ' created!')

    load_policy(opts)

    print('\nRestart the container with: "--security-opt label=type:' + opts['ContainerName'] + '.process" parameter')

if __name__ == "__main__":
    main()
