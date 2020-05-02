# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import asyncio

import pytest

import eapi
import eapi.messages

from tests.conftest import EAPI_TARGET

pytestmark = pytest.mark.skipif(not EAPI_TARGET, reason="target not set")


def test_execute(target, commands, auth):
    eapi.execute(target, commands=commands, auth=auth)

def test_enable(target, commands, auth):
    eapi.enable(target, commands=commands, auth=auth, secret="s3cr3t")

def test_execute_text(target, commands, auth):
    eapi.execute(target, commands=commands, auth=auth, encoding="text")


def test_execute_jsonerr(target, auth):

    response = eapi.execute(
        target, commands=["show hostname", "show bogus"], auth=auth, encoding="json")
    assert response.code > 0


def test_execute_err(target, auth):

    response = eapi.execute(target,
        commands=[
            "show hostname",
            "show bogus",
            "show running-config"
        ],
        encoding="text",
        auth=auth
    )
    assert response.code > 0


def test_configure(target, auth):

    eapi.configure(target, [
        "ip access-list standard DELETE_ME",
        "permit any"
    ], auth=auth)

    eapi.execute(target, ["show ip access-list DELETE_ME"], auth=auth)

    eapi.configure(target, [
        "no ip access-list DELETE_ME"
    ], auth=auth)


def test_watch(target, auth):
    def _cb(r, matched: bool):
        assert isinstance(r, eapi.messages.Response)
    
    eapi.watch(target, "show clock", callback=_cb, auth=auth, encoding="text", deadline=10)
    

@pytest.mark.asyncio
async def test_aexecute(target, commands, auth):
    resp = await eapi.aexecute(target, commands, auth=auth)

@pytest.mark.asyncio
async def test_awatch(target, auth):
    tasks = []

    def _cb(r, match: bool):
        assert isinstance(r, eapi.messages.Response)

    for c in ["show clock", "show hostname"]:
        tasks.append(
            eapi.awatch(target, c, callback=_cb, auth=auth, encoding="text", deadline=10)
        )
    
    await asyncio.wait(tasks)
    

