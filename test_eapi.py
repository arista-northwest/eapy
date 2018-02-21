# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import eapi
import pytest

EAPI_HOST = "tg219"

@pytest.fixture()
def session():
    return eapi.session(EAPI_HOST, auth=("admin", ""))

def test_execute(session):
    response = session.execute(["show version"])

    print(response)
