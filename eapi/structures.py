# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List, Optional, Tuple, Union
from typing_extensions import TypedDict

PromptedCommand = TypedDict('PromptedCommand', {
    'cmd': str,
    'input': str
})

Command = Union[str, PromptedCommand]

Params = TypedDict('Params', {
    'version': int,
    'cmds': List[Command],
    'format': str,
    'timestamps': bool
}, total=False)

Request = TypedDict('Request', {
    'id': str,
    'jsonrpc': str,
    'method': str,
    'params': Params
}, total=False)

Target = str # Union[str, Tuple[str, int]]

Auth = Tuple[str, Optional[str]]

Certificate = Optional[Union[str, Tuple[str, str]]]

# <int> or (<int>, <int>)
Timeout = Union[int, Tuple[int, int]]

RequestsOptions = TypedDict('RequestsOptions', {
    'auth': Auth,
    'timeout': Timeout,
    'cert': Certificate,
    'verify': bool
}, total=False)

