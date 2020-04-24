# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from eapi.messages import Response

def test_text_response(text_response):
    resp = Response.from_rpc_response(*text_response)
    assert resp.code == 0
    print(resp)

    assert "FQDN" in resp

def test_json_response(json_response):
    resp = Response.from_rpc_response(*json_response)
    assert resp.code == 0
    assert "fqdn" in resp

def test_errored_response(errored_response):
    resp = Response.from_rpc_response(*errored_response)
    assert resp.code == 1002

    assert "invalid" in resp

def test_errored_text_response(errored_text_response):
    resp = Response.from_rpc_response(*errored_text_response)
    assert resp.code == 1002
    assert "invalid" in resp