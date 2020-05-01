# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from sys import version
import click

import eapi
import eapi.environments

from eapi import util

@click.group()
@click.argument("target")
@click.option("--encoding", "-e", default="text")
@click.option("--username", "-u", default="admin", help="Username (default: admin")
@click.option("--password", "-p", default="", help="Username (default: <blank>")
@click.option("--cert", help="Client certificate file")
@click.option("--key", help="Private key file name")
@click.option("--verify/--no-verify", type=bool, default=True, help="verify SSL cert")
@click.pass_context
def main(ctx, target, encoding, username, password, cert, key, verify):
    pair = None
    auth = None
    
    if not verify:
        eapi.environments.SSL_WARNINGS = False

    if cert:
        pair = (cert, key)
    
    if not key:
        auth = (username, password)

    ctx.obj = {
        'encoding': encoding,
        'target': target,
        'auth': auth,
        'cert': pair,
        'verify': verify,
    }


@main.command()
@click.argument("commands", nargs=-1, required=True)
@click.pass_context
def execute(ctx, commands):
    
    target = ctx.obj["target"]
    encoding = ctx.obj["encoding"]
    auth = ctx.obj["auth"]
    cert = ctx.obj["cert"]
    verify = ctx.obj["verify"]

    resp = eapi.execute(target, commands,
        encoding=encoding,
        auth=auth,
        cert=cert,
        verify=verify)

    if encoding == "json":
        print(resp.json)
    else:
        print(resp.pretty)

@main.command()
@click.argument("command", nargs=1, required=True)
@click.option("--interval", "-i", type=int, default=None, help="Time between sends")
@click.option("--deadline", "-d", type=float, default=None, help="Limit how long to watch")
@click.option("--exclude / --no-exclude", default=False, help="Match if condition is FALSE")
@click.option("--condition", "-c", default=None, help="Pattern to search for, watch ends when matched")
@click.pass_context
def watch(ctx, command, interval, deadline, exclude, condition):
    
    target = ctx.obj["target"]
    encoding = ctx.obj["encoding"]
    auth = ctx.obj["auth"]
    cert = ctx.obj["cert"]
    verify = ctx.obj["verify"]

    def _cb(response, matched):
        if encoding == "json":
            print(response.json)
        else:
            util.clear_screen()
            print(f"Watching '{response[0].command}' in {response.target}")
            print()
            print(response[0])

    eapi.watch(target, command,
        callback=_cb,
        encoding=encoding,
        interval=interval,
        deadline=deadline,
        exclude=exclude,
        condition=condition,
        auth=auth,
        cert=cert,
        verify=verify)