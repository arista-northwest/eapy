# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import uuid
from urllib.parse import urlparse, urlunparse
from typing import Optional, Union, List

import eapi.sessions
from eapi.structures import Command, Params, Request, Target


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


def prepare_request(commands: List[Command], encoding: Optional[str] = None) -> Request:
    commands = prepare_cmd(commands)
    request_id = str(uuid.uuid4())

    if not encoding:
        encoding = eapi.sessions.ENCODING

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


# def prepare_url(target: Target, transport: Optional[str] = None,
#         path: Optional[str] = None) -> str:
#     """construct the url from path and transport"""

#     url = prepare_target(target, transport)
    
#     if isinstance(path, str):
#         if not path.startswith("/"):
#             path = "/" + path
#         url += path

#     return url


def prepare_target(target: Target, transport: Optional[str] = None) -> Target:
    """Normalize targe into a URL"""

    if isinstance(target, tuple):
        target = "%s:%d" % target

    if not transport:
        transport = eapi.sessions.TRANSPORT

    if "://" not in target:
        target = transport + "://" + target
    target = target.rstrip("/")
    return target

def get_target_domain(target: Target) -> str:
    parsed = urlparse(target)
    dom = parsed.netloc

    if ":" in dom:
        dom, _ = dom.split(":", 2)

    if "." not in dom:
        dom = dom + ".local"
    
    return dom

def zpad(keys, values, default=None):
    """zips two lits and pads the second to match the first in length"""

    keys_len = len(keys)
    values_len = len(values)

    if (keys_len < values_len):
        raise ValueError("keys must be as long or longer than values")

    values += [default] * (keys_len - values_len)

    return zip(keys, values)
