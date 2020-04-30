import asyncio

from sys import version
from eapi.util import prepare_request
import pytest

import eapi
import eapi.exceptions
import eapi.sessions
from eapi.messages import Target, Response
from eapi.sessions import Session, AsyncSession


from tests.conftest import EAPI_TARGET

pytestmark = pytest.mark.skipif(not EAPI_TARGET, reason="target not set")

def test_login(session, target):

    session.login(target)

    session.login(target)

    assert session.logged_in(target)

def test_login_err(target):
    t = Target.from_string(target)
    with Session() as sess:
        with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
            sess.login(target, auth=("sdfsf", "sfs"))
        
        with pytest.raises(eapi.exceptions.EapiHttpError):
            sess._send(t.url + "/login", None)

def test_send(session, target, auth):
    session.send(target, ["show hostname"])

def test_http_error(session, target):
    t = Target.from_string(target)
    with pytest.raises(eapi.exceptions.EapiHttpError):
        session._send(t.url + "/badpath", {})
 
def test_jsonrc_error(session, target):
    tgt = Target.from_string(target)
    req = prepare_request(["show hostname"])
    req["method"] = "bogus"
    resp = session._send(tgt.url + "/command-api", req)
    
    rresp = Response.from_rpc_response(tgt, req, resp.json())

    assert rresp.code < 0

def test_send_timeout(session, target):
    with pytest.raises(eapi.exceptions.EapiTimeoutError):
        session.send(target, ["bash timeout 30 sleep 30"], timeout=1)
    
    with pytest.raises(eapi.exceptions.EapiError):
        session.send("bogus", ["bash timeout 30 sleep 30"], timeout=1)

def test_context(target, auth):
    with eapi.Session() as sess:
        sess.login(target, auth=auth)
        sess.send(target, ["show hostname"])

def test_ssl_verify(starget, cert):

    sess = Session(cert=cert)
    with pytest.raises(eapi.exceptions.EapiError):  
        sess.send(starget, ["show users"])

# def test_getset(cert):
#     sess = Session()
#     sess.cert = cert
#     cert_ = sess.cert

#     assert cert_ == cert

#     sess.verify = False
#     verify = sess.verify

#     assert verify == False


def test_ssl(session, starget, cert):
    session.login(starget)
    session.send(starget, ["show users"])

def test_logout(target, auth):
    with Session() as sess:
        sess.login(target, auth=auth)
        sess.logout(target)

def test_logout_noexist(session):
    session.logout("bogus")

def test_unauth(session, target):
    with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
        session.login(target, auth=("l33t", "h3x0r"))
    
def test_send_noauth(session, target):
    sess = Session()
    with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
        sess.send(target, ["show hostname"])


@pytest.mark.asyncio
async def test_async(target, auth):
    
    targets = [target] * 4
    commands = [
        "show version",
        "show interfaces",
        "show running-config",
    ] * 3
    
    async with AsyncSession(auth=auth) as sess:
        tasks = []
        for t in targets:
            for c in commands:
                tasks.append(sess.send(t, [c], encoding="text"))
        
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 36