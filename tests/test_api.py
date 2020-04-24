# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import pytest

import eapi

from tests.conftest import EAPI_TARGET

pytestmark = pytest.mark.skipif(not EAPI_TARGET, reason="target not set")

eapi.SSL_WARNINGS = False


@pytest.fixture(autouse=True)
def login(target, auth):
    eapi.login(target, auth)

def test_login(target):
    assert eapi.session.logged_in(target)


def test_execute(target, commands):
    eapi.execute(target, commands=commands)



def test_execute_text(target, commands):
    eapi.execute(target, commands=commands, encoding="text")


def test_execute_jsonerr(target):

    response = eapi.execute(
        target, commands=["show hostname", "show bogus"], encoding="json")
    assert response.code > 0


def test_execute_err(target):

    response = eapi.execute(target, commands=[
                            "show hostname", "show bogus", "show running-config"], encoding="text")
    assert response.code > 0


def test_configure(target):

    eapi.configure(target, [
        "ip access-list standard DELETE_ME",
        "permit any"
    ])

    eapi.execute(target, ["show ip access-list DELETE_ME"])

    eapi.configure(target, [
        "no ip access-list DELETE_ME"
    ])


def test_logout(target):
    eapi.logout(target)
