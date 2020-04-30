# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import pytest

import eapi

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
    for resp in eapi.watch(target, "show clock", auth=auth, encoding="text", deadline=10):
        pass

