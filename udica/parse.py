#!/bin/python3

import json

def parse_inspect(data):
    try:
        json_rep = json.loads(data)
        if 'container=podman' not in json_rep[0]['Config']['Env']:
            for item in json_rep[0]['Mounts']:
                item['source'] = item['Source']
                if 'RW' in item:
                    item['options'] = 'rw'
                if 'RO' in item:
                    item['options'] = 'ro'

            temp_ports = []

            for item in json_rep[0]['NetworkSettings']['Ports']:
                container_port = item.split('/')
                host_port = json_rep[0]['NetworkSettings']['Ports'][item][0]['HostPort']
                new_port = {'hostPort':int(host_port), 'protocol':container_port[1]}
                temp_ports.append(new_port)

            del json_rep[0]['NetworkSettings']['Ports']

            json_rep[0]['NetworkSettings']['Ports'] = temp_ports

        return json_rep
    except:
        exit(2)

def parse_cap(data):
    return data.decode().split('\n')[1].split(',')
