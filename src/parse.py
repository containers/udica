#!/bin/python3

import json

def Parser(configFile):
    file = open(configFile)
    jsonRep = json.load(file)
    file.close()
    return jsonRep

def ParserCaps(ConfigFile):
    file = open(ConfigFile)
    CapabilitiesData = file.readline()
    CapabilitiesData = file.readline()
    file.close()
    return CapabilitiesData.rstrip().split(",")
