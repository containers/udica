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

def parse_inspect(data):
    try:
        json_rep = json.loads(data)
        if 'container=podman' not in json_rep[0]['Config']['Env']:
            for item in json_rep[0]['Mounts']:
                item['source'] = item['Source']
                if item['Mode'] == 'rw':
                    item['options'] = 'rw'
                if item['Mode'] == 'ro':
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

def parse_is_podman(data):
    try:
        json_rep = json.loads(data)
        if 'container=podman' in json_rep[0]['Config']['Env']:
            return 0
        else:
            return 1
    except:
        exit(2)
