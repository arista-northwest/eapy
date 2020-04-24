# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import uuid

from typing import Optional, Union, List
from eapi.structures import Command, Params, Request, Target, StrictTarget

def indent(spaces, text: str):
    indented = []
    for line in text.splitlines():
        indented.append(spaces + line)

    return "\n".join(indented)


def prepare_cmd(commands: Union[Command, List[Command]]):
    
    if isinstance(commands, (str, dict)):
        return prepare_cmd([commands])

    prepared = []
    for cmd in commands:
        if isinstance(cmd, str):
            prepared.append({"cmd": cmd, "input": ""})
        else:
            prepared.append(cmd)
    
    return prepared

def prepare_request(commands: List[Command], encoding: str) -> Request:
    commands = prepare_cmd(commands)
    request_id = str(uuid.uuid4())

    params: Params = {
        "version": 1,
        "format": encoding,
        "cmds": commands
    }

    req: Request = {
        "jsonrpc": "2.0",
        "method": "runCmds",
        "params": params,
        "id": request_id
    }
    return req

def prepare_url(target: Target, transport: str = "http", path="") -> str:
        """construct the url from path and transport"""

        host, port = prepare_target(target)

        url = "%s://%s" % (transport, host)

        if port is not None and port > 0:
            url += ":%d" % port

        if not path.startswith("/"):
            path = "/" + path

        return url + path

def prepare_target(target: Target, transport: str = "http") -> StrictTarget:
    """Normalize target"""
        
    host: str = ""
    port: Optional[int] = None

    if isinstance(target, str):
        
        if ":" in target:
            host, _port = target.split(":", 2)
            port = int(_port)
        else:
            host = target
    else:
        host, port = target

    return (host, port)

def zpad(keys, values, default=None):
    """zips two lits and pads the second to match the first in length"""

    keys_len = len(keys)
    values_len = len(values)

    if (keys_len < values_len):
        raise ValueError("keys must be as long or longer than values")
    
    values += [default] * (keys_len - values_len)

    return zip(keys, values)
