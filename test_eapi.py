# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import eapi
import pytest
import os

EAPI_HOST = os.environ.get('EAPI_HOST', "veos1")

# @pytest.fixture()
# def session():
#     return

def test_execute():
    sess = eapi.session(EAPI_HOST, auth=("admin", ""))
    response = sess.execute(["show hostname"])

def test_ssl_noverify():
    sess = eapi.session(EAPI_HOST, transport="https", verify=False)
    sess.execute(["show hostname"])

def test_ssl_verify():
    sess = eapi.session(EAPI_HOST, transport="https", verify=True)

    with pytest.raises(eapi.EapiError):
        sess.execute(["show hostname"])
