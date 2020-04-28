# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import click

import eapi
import eapi.sessions

from eapi import util

@click.group()
@click.argument("target")
@click.option("--username", "-u", default="admin", help="Username (default: admin")
@click.option("--password", "-p", default="", help="Username (default: <blank>")
@click.option("--cert", help="Client certificate file")
@click.option("--key", help="Private key file name")
@click.option("--verify/--no-verify", type=bool, default=True, help="verify SSL cert")
@click.pass_context
def main(ctx, target, username, password, cert, key, verify):
    pair = None
    auth = None
    
    if not verify:
        eapi.sessions.SSL_WARNINGS = False

    if cert:
        pair = (cert, key)
    
    if not key:
        auth = (username, password)

    ctx.obj = {
        'target': target
    }

    eapi.new(target, auth=auth, cert=pair, verify=verify)

@main.command()
@click.argument("commands", nargs=-1, required=True)
@click.option("--encoding", "-e", default="text")
@click.pass_context
def execute(ctx, commands, encoding="text"):
    
    target = ctx.obj["target"]
    resp = eapi.execute(target, commands, encoding=encoding)

    print(resp)

@main.command()
@click.argument("command", nargs=1, required=True)
@click.option("--encoding", "-e", default="text")
@click.option("--interval", "-i", type=int, default=None, help="Time between sends")
@click.option("--deadline", "-d", type=float, default=None, help="Limit how long to watch")
@click.option("--exclude / --no-exclude", default=False, help="Match if condition is FALSE")
@click.option("--condition", "-c", default=None, help="Pattern to search for, watch ends when matched")
@click.pass_context
def watch(ctx, command, encoding, interval, deadline, exclude, condition):
    target = ctx.obj["target"]

    def _cb(response):
        util.clear_screen()
        print("Watching: '%s' on %s" % (response.elements[0].command, response.target)) 
        print(response.elements[0].result.pretty)

    eapi.watch(target, command, encoding, interval, deadline, exclude, condition, _cb)