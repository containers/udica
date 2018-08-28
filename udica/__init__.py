import sys
import subprocess
import argparse

# import udica
from udica.parse import parse_inspect, parse_cap
from udica.policy import create_policy

def get_args():
    parser = argparse.ArgumentParser(description='Script generates SELinux policy for running container.')
    parser.add_argument(
        '-i', '--container-id', type=str, help='Running container ID', dest='ContainerID', required=True)
    parser.add_argument(
        '-n', '--name', type=str, help='Name for SELinux policy module', dest='ContainerName', required=True)
    parser.add_argument(
        '--full-network-access', help='Allow container full Network access ', required=False, dest='FullNetworkAccess', action='store_true')
    args = parser.parse_args()
    return vars(args)

def main():

    opts = get_args()

    container_inspect_data = subprocess.run(["podman", "inspect", opts['ContainerID']], capture_output=True).stdout.decode()
    container_caps_data = subprocess.run(["podman", "top", opts['ContainerID'], "capeff"], capture_output=True).stdout.decode()
    container_inspect = parse_inspect(container_inspect_data)
    container_caps = parse_cap(container_caps_data)

    container_mounts = container_inspect[0]['Mounts']
    container_ports = container_inspect[0]['NetworkSettings']['Ports']

    create_policy(opts,container_caps,container_mounts,container_ports)

    print('\nPolicy ' + opts['ContainerName'] + ' with container id ' + opts['ContainerID'] + ' created!\n')
    print('Please load this module using: # semodule -i ' + opts['ContainerName'] + '.cil')
    print('Start container with: "--security-opt label=type:' + opts['ContainerName'] + '.process" parameter')

if __name__ == "__main__":
    main()
