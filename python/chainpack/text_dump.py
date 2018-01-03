#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

try:
	import better_exceptions
except:
	pass

from value import *

import click

@click.command()
@click.argument('chainpack_file', type=click.File('rb'))
def dump(chainpack_file):
	import json
	py = ChainPackProtocol(chainpack_file.read()).read().toPython()
	print(json.JSONEncoder(indent=4, sort_keys=True).encode(py))

if __name__ == '__main__':
	dump()
