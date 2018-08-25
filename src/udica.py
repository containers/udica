#!/bin/python3

import sys
import os
import argparse

import parse
import policy

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

    os.system("podman inspect " + opts['ContainerID'] + "> /tmp/container.inspect")
    os.system("podman top " + opts['ContainerID'] + " capeff > /tmp/container.caps")

    ContainerInspect = parse.Parser("/tmp/container.inspect")
    ContainerCaps = parse.ParserCaps("/tmp/container.caps")

    ContainerMounts = ContainerInspect[0]['Mounts']
    ContainerPorts = ContainerInspect[0]['NetworkSettings']['Ports']

    policy.CreatePolicy(opts,ContainerCaps,ContainerMounts)

    print('\nPolicy ' + opts['ContainerName'] + ' with container id ' + opts['ContainerID'] + ' created!\n')
    print('Please load this module using: # semodule -i ' + opts['ContainerName'] + '.cil')
    print('Start container with: "--security-opt label=type:' + opts['ContainerName'] + '.process" parameter')

if __name__ == "__main__":
    main()
