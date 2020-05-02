import asyncio
import json

from sys import version

import httpx
import pytest

from eapi.util import prepare_request

import eapi
import eapi.exceptions
import eapi.sessions
from eapi.messages import Target, Response
from eapi.sessions import Session, AsyncSession


from tests.conftest import EAPI_TARGET

pytestmark = pytest.mark.skipif(not EAPI_TARGET, reason="target not set")


def test_login(session, target):

    session.login(target)
    assert session.logged_in(target)
    session.call(target, ["show version"])


def test_login_err(target):
    t = Target.from_string(target)
    with Session() as sess:
        with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
            sess.login(target, auth=("sdfsf", "sfs"))

        with pytest.raises(httpx.HTTPError):
            sess._call(t.url + "/login", None)


def test_call(session, target, auth):
    session.call(target, ["show hostname"])


def test_http_error(session, target):
    t = Target.from_string(target)
    with pytest.raises(eapi.exceptions.EapiPathNotFoundError):
        session._call(t.url + "/badpath", {})


def test_jsonrc_error(session, target):
    tgt = Target.from_string(target)
    req = prepare_request(["show hostname"])
    req["method"] = "bogus"
    resp = session._call(tgt.url + "/command-api", req)

    rresp = Response.from_rpc_response(tgt, req, resp.json())

    assert rresp.code < 0


def test_call_timeout(session, target):
    with pytest.raises(eapi.exceptions.EapiTimeoutError):
        session.call(target, ["bash timeout 30 sleep 30"], timeout=1)

    with pytest.raises(eapi.exceptions.EapiError):
        session.call("bogus", ["bash timeout 30 sleep 30"], timeout=1)


def test_context(target, auth):
    with eapi.Session() as sess:
        sess.login(target, auth=auth)
        sess.call(target, ["show hostname"])


def test_ssl_verify(starget, cert):

    sess = Session(cert=cert)
    with pytest.raises(eapi.exceptions.EapiError):
        sess.call(starget, ["show users"])


def test_ssl(session, starget, cert):
    session.login(starget)
    session.call(starget, ["show users"])


def test_logout(target, auth):
    with Session() as sess:
        sess.login(target, auth=auth)
        sess.logout(target)


def test_logout_noexist(session):
    session.logout("bogus")


def test_unauth(session, target):
    with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
        session.login(target, auth=("l33t", "h3x0r"))


def test_call_noauth(session, target):
    sess = Session()
    with pytest.raises(eapi.exceptions.EapiAuthenticationFailure):
        sess.call(target, ["show hostname"])


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
                tasks.append(sess.call(t, [c], encoding="text"))

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 36
