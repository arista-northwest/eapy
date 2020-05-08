# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import asyncio
import base64
import datetime
import json
import uuid
import re
import subprocess
import threading
import time

from typing import Union

from uvicorn.config import Config
from uvicorn.main import Server
from httpx import URL

import pytest


def _bash(encoding, *args):
    cmd = args[0].split()
    completed = subprocess.run(cmd, stdout=subprocess.PIPE)
    out = completed.stdout.decode('utf-8')
    responses = {
        "json": {
            "messages": [out]
        },
        "text": {
            "output": out
        }
    }

    return responses[encoding]


def _show_clock(encoding, *args):
    now = datetime.datetime.utcnow()
    responses = {
        "json": {
            "clockSource": {
                "local": True
            },
            "timezone": "UTC",
            "utcTime": now.timestamp(),
            "localTime": {
                "dayOfWeek": now.weekday(),
                "dayOfYear": now.timetuple().tm_yday,
                "sec": now.second,
                "min": now.minute,
                "hour": now.hour,
                "year": now.year,
                "dayOfMonth": now.day,
                "daylightSavingsAdjust": now.dst() or 0,
                "month": now.month
            }
        },
        "text": {"output": f"{now}\nTimezone: UTC\nClock source: local\n"}
    }
    return responses[encoding]


def _show_hostname(encoding, *args):
    responses = {
        "text": {"output": 'Hostname: localhost\n'
                           'FQDN:     localhost.localdomain\n'},
        "json": {
            'fqdn': 'localhost.localdomain',
            'hostname': 'localhost'
        }
    }
    return responses[encoding]


def _show_version(encoding, *args):
    responses = {
        "text": {"output":  'Arista DCS-7280CR2M-30-F\n'
                            'Hardware version:    20.01\n'
                            'Serial number:       JAS18140236\n'
                            'System MAC address:  7483.ef02.a6fb\n\n'
                            'Software image version: 4.23.2.1F-DPE\n'
                            'Architecture:           i686\n'
                            'Internal build version: 4.23.2.1F-DPE-16108061.42321F\n'
                            'Internal build ID:      73a5535d-c66e-4597-b6ed-8999e76b66ea\n\n'
                            'Uptime:                 1 weeks, 6 days, 16 hours and 35 minutes\n'
                            'Total memory:           32890040 kB\n'
                            'Free memory:            25851572 kB\n\n'},
        "json": {
            'memTotal': 32890040,
            'uptime': 1181670.77,
            'modelName': 'DCS-7280CR2M-30-F',
            'internalVersion': '4.23.2.1F-DPE-16108061.42321F',
            'mfgName': 'Arista',
            'serialNumber': 'JAS18140236',
            'systemMacAddress': '74:83:ef:02:a6:fb',
            'bootupTimestamp': 1586324536.0,
            'memFree': 25852932,
            'version': '4.23.2.1F-DPE',
            'architecture': 'i686',
            'isIntlVersion': False,
            'internalBuildId': '73a5535d-c66e-4597-b6ed-8999e76b66ea',
            'hardwareRevision': '20.01'
        }
    }
    return responses[encoding]


def _show_bogus(encoding, *args):
    responses = {
        "text": {"output": "% Invalid input (at token 1: 'bogus')\n"},
        "json": {}
    }
    return responses[encoding]


CMDS = [
    (re.compile(r"show version"), _show_version),
    (re.compile(r"show clock"), _show_clock),
    (re.compile(r"show hostname"), _show_hostname),
    (re.compile(r"bash timeout \d+ (.*)"), _bash)
]


def build_response(request):
    response = None
    results = []

    errored = False

    def _do_cmd(cmd, encoding):

        func = None
        result = None
        args = []

        for pat, func_ in CMDS:
            match = pat.search(cmd)
            if match:
                func = func_
                args = match.groups()
                break

        if func:
            result = func(encoding, *args)

        return result

    try:
        request_id = request["id"]
        encoding = request["params"]["format"]
        cmds = request["params"]["cmds"]

        if request["method"] != "runCmds":
            raise ValueError
        
        if not isinstance(cmds, list):
            raise ValueError

        for cmd in cmds:

            if isinstance(cmd, dict):
                cmd = cmd["cmd"]

            result = _do_cmd(cmd, encoding)

            if not result:
                errored = True
                results.append(_show_bogus(encoding))
                break
            else:
                results.append(result)

        response = {
            'jsonrpc': '2.0',
            'id': request_id
        }

        if errored:
            response["error"] = {
                "data": results,
                'message': "CLI command ... of ... failed: for some reason",
                'code': 1002
            }
        else:
            response["result"] = results
    except (KeyError, ValueError) as exc:
        # raise
        response = {
            'jsonrpc': '2.0',
            'id': None,
            'error': {
                'message': str(exc),
                'code': -32600
            }
        }

    return response


async def get_body(receive):
    body = b''
    more_body = True

    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)
    # print(body)
    return json.loads(body)


async def notfound_response(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 404,
            "headers": [
                [b"content-type", b"text/plain"]
            ]
        }
    )
    await send({
        "type": "http.response.body",
        "body": b"Page not found"
    })


async def unauthorized_response(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                [b"content-type", b"text/plain"]
            ]
        }
    )
    await send({
        "type": "http.response.body",
        "body": b"Unable to authenticate user: Bad username/password combination"
    })


async def eapi_response(scope, receive, send):

    body = await get_body(receive)

    response = build_response(body)

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]]
        }
    )
    await send({"type": "http.response.body", "body": bytes(json.dumps(response), "utf-8")})


async def logout_response(scope, receive, send):

    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"application/json"]]
    })
    await send({"type": "http.response.body", "body": b"{\"Logout\": true}"})


async def login_response(scope, receive, send):

    authorized = True
    no_cookie = False
    none_cookie = False
    not_found = False

    data = await get_body(receive)

    if not data:
        raise ValueError("No login data")

    username = data.get("username", None)
    password = data.get("password", None)

    if password == "nocookie":
        no_cookie = True
    if password == "nonecookie":
        none_cookie = True
    if password == "notfound":
        not_found = True
    elif username != password:
        authorized = False

    def _gen_cookie():
        tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        expries = tomorrow.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        session_id = str(uuid.uuid4())
        return bytes(f"Session={session_id};Expires={expries};Path=/;HttpOnly", "utf-8")

    if not_found:
        await notfound_response(scope, receive, send)

    elif authorized:
        headers = [
            [b"content-type", b"application/json"],

        ]

        # Simulate no cookie or "None" cookie
        if no_cookie:
            pass
        elif none_cookie:
            headers.append([b"set-cookie", b"None"])
        else:
            headers.append([b"set-cookie", _gen_cookie()])

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": headers
            }
        )
        await send({"type": "http.response.body", "body": b"{\"Login\": true}"})
    else:
        await unauthorized_response(scope, receive, send)


def get_header(header: bytes, headers):
    return dict(headers).get(header)

def decode_auth(headers):
    auth = None
    header = get_header(b"authorization", headers)
    if header:
        header = header.decode("utf-8")
        match = re.search("Basic (.*)", header)
        if match:
            userpass = base64.b64decode(match.group(1)).decode("utf-8")
            auth = tuple(userpass.split(":"))

    return auth


async def app(scope, receive, send):
    assert scope["type"] == "http"

    auth = decode_auth(scope["headers"])

    # for testing the correct password is the username
    if auth and auth[0] != auth[1]: 
        await unauthorized_response(scope, receive, send)
    
    if scope["path"].startswith("/login"):
        await login_response(scope, receive, send)
    elif scope["path"].startswith("/logout"):
        await logout_response(scope, receive, send)
    elif scope["path"].startswith("/command-api"):
        await eapi_response(scope, receive, send)
    else:
        await notfound_response(scope, receive, send)


class TestServer(Server):
    @property
    def url(self) -> URL:
        protocol = "https" if self.config.is_ssl else "http"
        return URL(f"{protocol}://{self.config.host}:{self.config.port}/")

    def install_signal_handlers(self) -> None:
        # Disable the default installation of handlers for signals such as SIGTERM,
        # because it can only be done in the main thread.
        pass

    async def serve(self, sockets=None):
        self.restart_requested = asyncio.Event()

        loop = asyncio.get_event_loop()
        tasks = {
            loop.create_task(super().serve(sockets=sockets)),
            loop.create_task(self.watch_restarts()),
        }
        await asyncio.wait(tasks)

    async def restart(self) -> None:
        # This coroutine may be called from a different thread than the one the
        # server is running on, and from an async environment that's not asyncio.
        # For this reason, we use an event to coordinate with the server
        # instead of calling shutdown()/startup() directly, and should not make
        # any asyncio-specific operations.
        self.started = False
        self.restart_requested.set()
        while not self.started:
            await asyncio.sleep(0.2)

    async def watch_restarts(self):
        while True:
            if self.should_exit:
                return

            try:
                await asyncio.wait_for(self.restart_requested.wait(), timeout=0.1)
            except asyncio.TimeoutError:
                continue

            self.restart_requested.clear()
            await self.shutdown()
            await self.startup()


def serve_in_thread(server: Server):
    thread = threading.Thread(target=server.run)
    thread.start()
    try:
        while not server.started:
            time.sleep(1e-3)
        yield server
    finally:
        server.should_exit = True
        thread.join()


@pytest.fixture(scope="session")
def server():
    config = Config(app=app, lifespan="off", loop="asyncio")
    server = TestServer(config=config)
    yield from serve_in_thread(server)


@pytest.fixture(scope="session")
def https_server(cert_pem_file, cert_private_key_file):
    config = Config(
        app=app,
        lifespan="off",
        ssl_certfile=cert_pem_file,
        ssl_keyfile=cert_private_key_file,
        host="localhost",
        port=8001,
        loop="asyncio"
    )
    server = TestServer(config=config)
    yield from serve_in_thread(server)
