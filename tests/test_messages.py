# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import pytest

from eapi.messages import Response, ResponseElem, Target, TextResult, JsonResult

def test_text_result(text_response):
    r = TextResult(text_response[-1]["result"][1]["output"])
    str(r)
    r.pretty

def test_json_result(json_response):
    
    r = JsonResult(json_response[-1]["result"][1])
    str(r)
    r.pretty
    len(r)
    for k,v in r.items():
        pass

def test_response_elem(json_response, text_response):
    _, request, response = json_response

    c = request["params"]["cmds"][-1]
    r = response["result"][1]
    t = text_response[-1]["result"][1]["output"]
    ResponseElem(c["cmd"], JsonResult(r))
    e = ResponseElem(c, JsonResult(r))
    str(e)
    e.to_dict()

    e = ResponseElem(c, TextResult(t))
    str(e)
    e.to_dict()

def test_text_response(text_response):
    resp = Response.from_rpc_response(*text_response)
    assert resp.code == 0
    assert "FQDN" in resp
    assert "target" in resp
    
    resp.to_dict()
    for elem in resp:
        assert isinstance(elem, ResponseElem)

def test_json_response(json_response):
    resp = Response.from_rpc_response(*json_response)
    assert resp.code == 0
    assert "fqdn" in resp
    resp.to_dict()
    for elem in resp:
        assert isinstance(elem, ResponseElem)

def test_errored_response(errored_response):
    resp = Response.from_rpc_response(*errored_response)
    assert resp.code == 1002

    assert "invalid" in resp
    resp.to_dict()
    for elem in iter(resp):
        assert isinstance(elem, ResponseElem)

def test_errored_text_response(errored_text_response):
    resp = Response.from_rpc_response(*errored_text_response)
    assert resp.code == 1002
    assert "invalid" in resp
    resp.to_dict()
    for elem in resp:
        assert isinstance(elem, ResponseElem)


def test_target(target, starget):

    t = Target.from_string(target)
    t = Target.from_string(t)
    assert str(t).startswith("http:")
    t = Target.from_string(starget)
    assert str(t).startswith("https:")

    with pytest.raises(ValueError):
        t = Target.from_string(":///_10:600000")


    t = Target("host.lab", "http", 80)
    assert str(t) == "http://host.lab"

    assert t.domain == "host.lab"

    t = Target("host", "http", 8080)
    assert str(t) == "http://host:8080"

    assert t.domain == "host.local"

    with pytest.raises(ValueError):
        Target("host", transport="bogus", port=6000)

    with pytest.raises(ValueError):
        Target("host", transport="http", port=600000)

