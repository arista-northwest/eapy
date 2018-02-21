# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import eapi
import os
import pytest

eapi.EAPI_SSL_WARNINGS = False

EAPI_HOST = os.environ.get('EAPI_HOST', "veos1")
EAPI_CLIENT_CERT = os.environ.get('EAPI_CLIENT_CERT')
EAPI_CLIENT_KEY = os.environ.get('EAPI_CLIENT_KEY')

def test_execute():
    sess = eapi.session(EAPI_HOST)
    response = sess.execute(["show hostname"])

def test_ssl_verify():
    sess = eapi.session(EAPI_HOST, transport="https", verify=True)

    with pytest.raises(eapi.EapiError):
        sess.execute(["show hostname"])

def test_ssl_noverify():
    sess = eapi.session(EAPI_HOST, transport="https", verify=False)
    sess.execute(["show hostname"])

def test_ssl_client_cert():
    if not (EAPI_CLIENT_CERT and EAPI_CLIENT_KEY):
        pytest.skip("certificate/key pair is not set")

    sess = eapi.session(EAPI_HOST, cert=(EAPI_CLIENT_CERT, EAPI_CLIENT_KEY),
                        transport="https", verify=False)

    sess.execute(["show hostname"])
