# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import uuid

import os
from typing import Optional, Union, List

import eapi.sessions
from eapi.types import Command, Params, Request

from eapi.environments import EAPI_DEFAULT_ENCODING

def clear_screen() -> None:
    if os.name == 'nt': 
        os.system('cls')
    else: 
        os.system('clear')

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
        encoding = EAPI_DEFAULT_ENCODING

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


def zpad(keys, values, default=None):
    """zips two lits and pads the second to match the first in length"""

    keys_len = len(keys)
    values_len = len(values)

    if (keys_len < values_len):
        raise ValueError("keys must be as long or longer than values")

    values += [default] * (keys_len - values_len)

    return zip(keys, values)
