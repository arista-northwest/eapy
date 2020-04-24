# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import uuid
import urllib3
import warnings

from typing import Dict, List, MutableMapping, Optional
from typing_extensions import Final

import requests

from eapi.util import prepare_request, prepare_target, prepare_url
from eapi.exceptions import EapiAuthenticationFailure, EapiError, \
                            EapiHttpError, EapiTimeoutError
from eapi.structures import Auth, Command, RequestsOptions, \
                            StrictTarget, Target, Timeout
from eapi.messages import Response

# # The default username password for all Aristas is 'admin' with no password
# AUTH: Auth = ("admin", "")

# Specifies the default result encoding.  The alternative is 'text'
ENCODING: str = "json"

# Specifies whether to add timestamps for each command by default
INCLUDE_TIMESTAMPS: bool = False

# This should not need to change.  All responses are JSON
SESSION_HEADERS: Final[dict] = {"Content-Type": "application/json"}

# Set this to false to allow untrusted HTTPS/SSL
SSL_VERIFY: bool = True

# Set this to false to supress warnings about untrusted HTTPS/SSL
SSL_WARNINGS: bool = True

# Some eAPI operations may take some time so a longer 'read' timeout is used
# e.g. show running-config
# See: https://requests.readthedocs.io/en/master/user/advanced/#timeouts
TIMEOUT: Timeout = (5, 30)

# By default eapi uses HTTP.  HTTPS ('https') is also supported
TRANSPORT: str = "http"


class DisableSslWarnings(object):
    """Context manager to disable then re-enable SSL warnings"""
    #pylint: disable=R0903

    def __init__(self):
        self.category = urllib3.exceptions.InsecureRequestWarning

    def __enter__(self):
        if not SSL_WARNINGS:
            warnings.simplefilter('ignore', self.category)

    def __exit__(self, *args):
        warnings.simplefilter('default', self.category)

class EapiSession():
    def __init__(self, transport: str = TRANSPORT,
            options: RequestsOptions = {}):
        # self.target = prepare_target(target)
        self.transport = transport
        self.options = options
    
    @property
    def params(self) -> tuple:
        return (self.transport, self.options)

class EapiSessionStore(MutableMapping):
    def __init__(self):
        self._data: Dict[StrictTarget, EapiSession] = {}

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, target: Target) -> EapiSession:
        target = prepare_target(target)
        return self._data[target]

    def __setitem__(self, target: Target, eapi_session: EapiSession):
        target = prepare_target(target)
        self._data[target] = eapi_session
    
    def __delitem__(self, target: Target):
        target = prepare_target(target)
        del self._data[target]
    
    def __len__(self):
        return len(self._data)

class Session(object):
    def __init__(self):
        # use a requests Session to manage state
        self._session = requests.Session()

        # every request should send the same headers
        self._session.headers = SESSION_HEADERS
        
        # store parameters for future requests
        self._eapi_sessions = EapiSessionStore()

    def logged_in(self, target):
        """determines if session cookie is set"""
        host, _ = prepare_target(target)

        if "." not in host:
            host = host + ".local"
        
        cookie = self._session.cookies.get("Session", domain=host)
        return True if cookie else False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown()

    def shutdown(self):
        """shutdown the underlying requests session"""
        self._session.close()
    
    def new(self, target: StrictTarget, auth: Auth, transport: str = TRANSPORT, options: RequestsOptions = {}) -> None:
        """Create a new eAPI session

        :param target: eAPI target (host, port)
        :param type: StrictTarget
        :param auth: tuple containing a username and password
        :param type: Auth
        :param transport: http or https
        :param type: str
        :param options: pass through `requests` options
        :param type: RequestsOptions

        :
        """
        if "auth" in options:
            raise ValueError("please use the `auth` parameter")
        
        if "certificate" not in options:
            self._login(target, auth, transport, options)
                
        
        self._eapi_sessions[target] = EapiSession(transport, options)
    login = new
    
    def _login(self, target: Target, auth: Auth,
            transport: str = TRANSPORT, options: RequestsOptions = {}) -> bool:
        """Session based authentication"""
        
        if self.logged_in(target):
            return True
        
        username, password = auth
        payload = {"username": username, "password": password}
        
        url = prepare_url(target, transport, "/login")

        resp = self._send(url, data=payload, options=options)

        if resp.status_code == 404:
            # fall back to basic auth if /login is not found or Session key is
            # missing
            pass
        elif not resp.ok:
            raise EapiError(resp.reason)

        
        if "Session" not in resp.cookies:
            warnings.warn(("Got a good response, but no 'Session' found in "
                           "cookies. Using fallback auth."))

        elif resp.cookies["Session"] == "None":
            # this is weird... investigate further
            warnings.warn("Got cookie Session='None' in response?! "
                          "Using fallback auth.")

        return True

    def close(self, target: Target):
        """destroys the session"""
        
        transport, options = self._eapi_sessions.get(target).params

        if self.logged_in(target):
            url = prepare_url(target, transport, "/logout")
            self._send(url, data={}, options=options)
    logout = close

    def send(self, target: Target, commands: List[Command],
            encoding: str = ENCODING,
            transport: str = "",
            options: RequestsOptions = {}):
        
        # get session defaults (set at login)
        _transport, _options = self._eapi_sessions.get(target).params

        if not transport:
            transport = _transport
        
        _options.update(options)
        options = _options

        request = prepare_request(commands, encoding)
        url = prepare_url(target, transport, "/command-api")

        if not self.logged_in(target):
            if "auth" not in options:
                options["auth"] = AUTH

        response = self._send(url, data=request, options=options)

        return Response.from_rpc_response(target, request, response.json())

    def _send(self, url, data, options: RequestsOptions = {}):
        """Sends the request to EAPI"""

        response = None
        
        if "verify" not in options:
            options["verify"] = SSL_VERIFY

        if "timeout" not in options:
            options["timeout"] = TIMEOUT
        
        try:
            with DisableSslWarnings():
                response = self._session.post(url, data=json.dumps(data),
                                              **options)
        except requests.Timeout as exc:
            raise EapiTimeoutError(str(exc))
        except requests.ConnectionError as exc:
            raise EapiError(str(exc))

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if response.status_code == 401:
                raise EapiAuthenticationFailure(str(exc))
            raise EapiHttpError(str(exc))

        return response


# session singleton(ish)
session = Session()