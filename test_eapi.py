# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import eapi
import os
import pytest
import time

from pprint import pprint

EAPI_HOST = os.environ.get('EAPI_HOST', "veos")
EAPI_USER = os.environ.get('EAPI_USER', "admin")
EAPI_PASSWORD = os.environ.get('EAPI_PASSWORD', "")
EAPI_CLIENT_CERT = os.environ.get('EAPI_CLIENT_CERT')
EAPI_CLIENT_KEY = os.environ.get('EAPI_CLIENT_KEY')
EAPI_CA_CERT = os.environ.get('EAPI_CA_CERT', False)

eapi.SSL_WARNINGS = False
eapi.DEFAULT_AUTH = (EAPI_USER, EAPI_PASSWORD)

commands = ["show hostname", "show version"]

def test_execute():
    sess = eapi.session(EAPI_HOST)
    response = sess.execute(commands)

    response.raise_for_error()

    # print(str(response))

    assert response.code == 0, "Expected a clean response"

def test_response():
    #time.sleep(5)
    with eapi.session(EAPI_HOST) as sess:
        response = sess.execute(commands)
        
        assert hasattr(response, "result")

        assert "result" in response.to_dict()

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
                        transport="https", verify=EAPI_CA_CERT)

    sess.execute(commands)

def test_to_string():
    with eapi.session(EAPI_HOST) as sess:
        response = sess.execute(commands, encoding="json")
        pprint(response.to_dict())
        print(str(response))
        print(response.to_json(2, (', ', ': ')))