# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import click

import eapi
import eapi.sessions

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
@click.argument("commands", nargs=-1)
@click.option("--encoding", "-e", default="text")
@click.pass_context
def execute(ctx, commands, encoding="text"):
    
    target = ctx.obj["target"]
    resp = eapi.execute(target, commands, encoding=encoding)

    print(resp)