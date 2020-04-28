
from eapi.util import prepare_request
import pytest

import eapi
import eapi.exceptions
import eapi.sessions
from eapi.messages import Target, Response
from eapi.sessions import session


from tests.conftest import EAPI_TARGET

pytestmark = pytest.mark.skipif(not EAPI_TARGET, reason="target not set")

def test_session_new(target, auth):

    session.new(target, auth=auth)

    session.new(target, auth=auth)

def test_session_send(target):
    session.send(target, ["show hostname"])

def test_http_error(target):
    t = Target.from_string(target)
    with pytest.raises(eapi.exceptions.EapiHttpError):
        session._send(t.url + "/badpath", {})
 
def test_jsonrc_error(target):
    tgt = Target.from_string(target)
    req = prepare_request(["show hostname"])
    req["method"] = "bogus"
    resp = session._send(tgt.url + "/command-api", req)
    
    rresp = Response.from_rpc_response(tgt, req, resp.json())

    assert rresp.code < 0

def test_send_timeout(target):
    with pytest.raises(eapi.exceptions.EapiError):
        session.send(target, ["bash timeout 30 sleep 30"], timeout=1)
    
    with pytest.raises(eapi.exceptions.EapiError):
        session.send("bogus", ["bash timeout 30 sleep 30"], timeout=1)

def test_context(target, auth):
    with eapi.Session() as sess:
        sess.new(target, auth=auth)
        sess.send(target, ["show hostname"])

def test_session_ssl_verify(starget, certificate):
    session.new(starget, cert=certificate)
    with pytest.raises(eapi.exceptions.EapiError):  
        session.send(starget, ["show users"])

def test_session_ssl(starget, certificate):
    session.new(starget, cert=certificate, verify=False)
    session.send(starget, ["show users"])

def test_session_close(target):
    session.close(target)

def test_session_close_noexist():
    session.close("bogus")

def test_session_unauth(target):
    with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
        session.new(target, auth=("l33t", "h3x0r"))
    
def test_session_send_noauth(target):
    with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
        session.send(target, ["show hostname"])

