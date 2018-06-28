#! /bin/sh

_CONFIG_FILE=${CONFIG_FILE:-/config-cleanup.yml}

python cleanup.py -c $_CONFIG_FILE
