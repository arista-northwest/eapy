# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import eapi
import os
import pytest
import time

eapi.SSL_WARNINGS = False

EAPI_HOST = os.environ.get('EAPI_HOST', "veos")
EAPI_CLIENT_CERT = os.environ.get('EAPI_CLIENT_CERT')
EAPI_CLIENT_KEY = os.environ.get('EAPI_CLIENT_KEY')
commands = ["show hostname"]

def test_execute():
    sess = eapi.session(EAPI_HOST)
    response = sess.execute(commands)

    response.raise_for_error()

    assert response.code == 0, "Expected a clean response"

def test_response():
    #time.sleep(5)
    with eapi.session(EAPI_HOST) as sess:
        response = sess.execute(commands)

        assert hasattr(response, "output")

        assert "output" in response.to_dict()

def test_with_context():
    with eapi.session(EAPI_HOST) as sess:
        sess.execute(commands)
#
def test_login():
    sess = eapi.session(EAPI_HOST)
    sess.login()
    assert sess.logged_in, "expected to be logged in..."

def test_prepare_url():
    sess = eapi.session(EAPI_HOST)
    sess.prepare_url(path="/fake-path")

def test_invalid_login():
    sess = eapi.session(EAPI_HOST, auth=("baduser", "baspass"))

    with pytest.raises(eapi.EapiAuthenticationFailure):
        sess.login()

def test_execute_bad_command():
    sess = eapi.session(EAPI_HOST)
    response = sess.execute(["show hostname", "show bogus"])

    with pytest.raises(eapi.EapiResponseError):
        response.raise_for_error()

    assert response.code == 1002, "Expected an errored response"

def test_ssl_verify():
    sess = eapi.session(EAPI_HOST, transport="https", verify=True)

    with pytest.raises(eapi.EapiError):
        sess.execute(commands)

def test_ssl_noverify():
    sess = eapi.session(EAPI_HOST, transport="https", verify=False)
    sess.execute(commands)

def test_ssl_client_cert():
    if not (EAPI_CLIENT_CERT and EAPI_CLIENT_KEY):
        pytest.skip("certificate/key pair is not set")

    sess = eapi.session(EAPI_HOST, cert=(EAPI_CLIENT_CERT, EAPI_CLIENT_KEY),
                        transport="https", verify=False)

    sess.execute(commands)
