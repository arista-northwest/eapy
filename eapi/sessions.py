# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import urllib3
import warnings

from urllib.parse import urlparse
from typing import Dict, List, MutableMapping, Optional

import requests

#from eapi.constants import ENCODING, SSL_VERIFY, SSL_WARNINGS, TIMEOUT, TRANSPORT
from eapi.util import get_target_domain, prepare_request, prepare_target
from eapi.exceptions import EapiAuthenticationFailure, EapiError, \
    EapiHttpError, EapiTimeoutError
from eapi.structures import Auth, Certificate, Command, RequestsOptions, \
    Target
from eapi.messages import Response

from eapi.structures import Timeout

# # The default username password for all Aristas is 'admin' with no password
# AUTH: Auth = ("admin", "")

# Specifies the default result encoding.  The alternative is 'text'
ENCODING: str = "json"

# Specifies whether to add timestamps for each command by default
INCLUDE_TIMESTAMPS: bool = False

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

# PORTS: Dict[str, int] = {"http": 80, "https": 443}

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
                 **options: RequestsOptions):
        self.transport = transport
        self.options = options

    @property
    def params(self) -> tuple:
        return (self.transport, self.options)


class EapiSessionStore(MutableMapping):
    def __init__(self):
        self._data: Dict[str, EapiSession] = {}

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, target: Target) -> EapiSession:
        domain = get_target_domain(target)
        return self._data[domain]

    def __setitem__(self, target: Target, eapi_session: EapiSession):
        domain = get_target_domain(target)
        self._data[domain] = eapi_session

    def __delitem__(self, target: Target):
        domain = get_target_domain(target)
        del self._data[domain]

    def __len__(self):
        return len(self._data)



class Session(object):
    def __init__(self):
        # use a requests Session to manage state
        self._session = requests.Session()

        # every request should send the same headers
        # This should not need to change.  All responses are JSON
        self._session.headers = {"Content-Type": "application/json"}

        # store parameters for future requests
        self._eapi_sessions = EapiSessionStore()

    def logged_in(self, target: Target, transport: Optional[str] = None):
        """determines if session cookie is set"""
        target = prepare_target(target)
        domain = get_target_domain(target)

        cookie = self._session.cookies.get("Session", domain=domain)
        
        return True if cookie else False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown()

    def shutdown(self):
        """shutdown the underlying requests session"""
        self._session.close()

    def new(self, target: Target, transport: Optional[str] = None,
            auth: Optional[Auth] = None, cert: Optional[Certificate] = None,
            **kwargs) -> None:
        """Create a new eAPI session

        :param target: eAPI target (host, port)
        :param type: Target
        :param transport: http or https
        :param type: str
        :param auth: username, password tuple
        :param type: Auth
        :param cert: client certificate or (certificate, key) tuple
        :param type: Certificate
        :param \*\*options: other pass through `requests` options
        :param type: RequestsOptions

        """
        target = prepare_target(target, transport=transport)

        if auth:
            if not self._login(target, auth, **kwargs):
                kwargs["auth"] = auth
        elif cert:
            transport = "https"
            kwargs["cert"] = cert

        if not transport:
            transport = TRANSPORT

        target = prepare_target(target, transport=transport)

        self._eapi_sessions[target] = EapiSession(transport, **kwargs)
    login = new

    def _login(self, target: Target, auth, **kwargs) -> bool:
        """Session based authentication"""

        if self.logged_in(target):
            return True

        username, password = auth
        payload = {"username": username, "password": password}

        resp = self._send(target + "/login", data=payload, **kwargs)

        if resp.status_code == 404:
            # fall back to basic auth if /login is not found or Session key is
            # missing
            return False
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

    def close(self, target: Target, transport: Optional[str] = None):
        """destroys the session"""

        target = prepare_target(target, transport=transport)
        
        _, options = self._eapi_sessions.get(target).params

        if self.logged_in(target):
            self._send(target + "/logout", data={}, **options)
    
    logout = close

    def send(self, target: Target, commands: List[Command],
            encoding: str = ENCODING, transport: Optional[str] = None,
            **options: RequestsOptions):

        target = prepare_target(target, transport=transport)

        # get session defaults (set at login)
        _transport, _options = self._eapi_sessions.get(target).params

        if not transport:
            transport = _transport

        _options.update(options)
        options = _options

        request = prepare_request(commands, encoding)

        response = self._send(target + "/command-api", data=request, **options)

        return Response.from_rpc_response(target, request, response.json())

    def _send(self, url, data, **options):
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
