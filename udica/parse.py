#!/bin/python3

import json

def parse_inspect(data):
    try:
        json_rep = json.loads(data)
        return json_rep
    except:
        exit(2)

def parse_cap(data):
    return data.decode().split('\n')[1].split(',')
