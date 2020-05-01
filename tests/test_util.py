
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import Tuple, Optional
import pytest

import eapi.sessions
from eapi.util import indent, prepare_cmd, prepare_request, zpad


@pytest.mark.parametrize("text", [
    "a\nb\nc\nd\nf"
])
def test_indent(text):
    indent(" " * 10, text)


@pytest.mark.parametrize("cmd", [
    "show some stuff",
    {"cmd": "show secret stuff", "input": "s3c3rt"},
    ["show some stuff", {"cmd": "show secret stuff", "input": "s3c3rt"}]
])
def test_prepare_cmd(cmd):
    commands = prepare_cmd(cmd)
    for cmd in commands:
        assert "cmd" in cmd
        assert "input" in cmd
        assert len(cmd["cmd"]) > 0


def test_prepare_request(reqwest):

    assert reqwest["jsonrpc"] == "2.0"
    assert reqwest["method"] == "runCmds"
    assert isinstance(reqwest["id"], str)
    assert reqwest["params"]["version"] == 1
    assert reqwest["params"]["format"] in ("json", "text")
    for command in reqwest["params"]["cmds"]:
        assert "cmd" in command
        assert "input" in command
        assert len(command["cmd"]) > 0

    p = prepare_request(["show stuff"])
    assert p["params"]["format"] == eapi.environments.EAPI_DEFAULT_ENCODING


def test_zpad():
    a = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    z = ['z', 'y', 'x', 'w']

    r = list(zpad(a[:], z[:], None))
    assert len(r) == len(a)

    with pytest.raises(ValueError):
        zpad(z[:], a[:], None)
