#!/bin/python3

import json

def parse_inspect(config_file):
    file = open(config_file)
    json_rep = json.load(file)
    file.close()
    return json_rep

def parse_cap(config_file):
    file = open(config_file)
    caps = file.readline()
    caps = file.readline()
    file.close()
    return caps.rstrip().split(",")
