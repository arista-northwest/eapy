# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import urllib3
import warnings

from typing import Dict, List, Optional, Union

import httpx

from eapi.util import prepare_request
from eapi.exceptions import EapiAuthenticationFailure, EapiError, \
    EapiHttpError, EapiTimeoutError
from eapi.structures import Auth, Certificate, Command

from eapi.messages import Response, Target

from eapi.structures import Timeout

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


class Session(object):
    def __init__(self,
            auth: Optional[Auth] = None,
            cert: Optional[Certificate] = None,
            verify: Optional[bool] = None,
            **kwargs):
       
        if verify is None:
            verify = SSL_VERIFY

        # use a httpx Session to manage state
        self._session = httpx.Client(
            auth=auth,
            cert=cert,
            headers={"Content-Type": "application/json"},
            verify=verify,
            **kwargs
        )

        # store parameters for future requests
        self._eapi_sessions: Dict[str, dict] = {}

    def logged_in(self, 
            target: Union[str, Target],
            transport: Optional[str] = None
        ) -> bool:
        """determines if session cookie is set"""
        target_: Target = Target.from_string(target)

        cookie = self._session.cookies.get("Session", domain=target_.domain)

        return True if cookie else False

    @property
    def cert(self) -> Certificate:
        return self._session.cert
    
    @cert.setter
    def cert(self, cert: Certificate) -> None:
        self._session.cert = cert
    
    @property
    def verify(self) -> bool:
        return self._session.verify
    
    @verify.setter
    def verify(self, verify: bool):
        self._session.verify = verify

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *args) -> None:
        self.shutdown()

    def _send(self, url, data, **options) -> httpx.Response:
        """Sends the request to EAPI"""

        response = None

        if "timeout" not in options:
            options["timeout"] = TIMEOUT

        try:
            with DisableSslWarnings():
                response = self._session.post(url, data=json.dumps(data),
                                              **options)
        except urllib3.exceptions.ReadTimeoutError as exc:
            raise EapiTimeoutError(str(exc))
        except httpx.HTTPError as exc:
            raise EapiError(str(exc))

        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            if response.status_code == 401:
                raise EapiAuthenticationFailure(str(exc))
            raise EapiHttpError(str(exc))

        return response

    def logout(self, target: Union[str, Target]) -> None:
        """Log out of an eAPI session

        :param target: eAPI target (host, port)
        :param type: Target

        """

        options = {}
        target_: Target = Target.from_string(target)
        
        if target_.domain in self._eapi_sessions:
            options = self._eapi_sessions[target_.domain]
            del self._eapi_sessions[target_.domain]

        if self.logged_in(target):
            self._send(target_.url + "/logout", data={}, **options)

    def login(self, target: Union[str, Target], auth: Optional[Auth] = None,
            **kwargs) -> None:
        """Login to an eAPI session

        :param target: eAPI target (host, port)
        :param type: Target
        :param auth: username, password tuple
        :param type: Auth
        :param cert: client certificate or (certificate, key) tuple
        :param type: Certificate
        :param \*\*options: other pass through `httpx` options
        :param type: HttpxOptions

        """
        target_: Target = Target.from_string(target)

        if self.logged_in(target):
            return

        username, password = auth or self._session.auth
        payload = {"username": username, "password": password}

        resp = self._send(target_.url + "/login", data=payload, **kwargs)

        if resp.status_code == 404:
            # Older versions do not have the login endpoint.
            # fall back to basic auth if /login is not found
            pass
        elif resp.status_code != 200:
            raise EapiError(f"{resp.status_code} {resp.reason_phrase}")

        if "Session" not in resp.cookies:
            warnings.warn(("Got a good response, but no 'Session' found in "
                           "cookies. Using fallback auth."))
        elif resp.cookies["Session"] == "None":
            # this is weird... investigate further
            warnings.warn("Got cookie Session='None' in response?! "
                          "Using fallback auth.")

        if not self.logged_in(target):
            # store auth if login fails (without throwing an exception)
            kwargs["auth"] = auth

        self._eapi_sessions[target_.domain] = kwargs

    def send(self, target: Union[str, Target], commands: List[Command],
             encoding: Optional[str] = None, **kwargs):
        """Send commands to an eAPI target

        :param target: eAPI target (host, port)
        :param type: Target
        :param commands: List of `Command` objects
        :param type: list
        :param encoding: response encoding 'json' or 'text' (default: json)
        :param \*\*kwargs: other pass through `httpx` options
        :param type: dict

        """

        target_: Target = Target.from_string(target)

        # get session defaults (set at login)
        _options = self._eapi_sessions.get(target_.domain) or {}

        _options.update(kwargs)
        options = _options

        if not encoding:
            encoding = ENCODING
        
        request = prepare_request(commands, encoding)

        response = self._send(target_.url + "/command-api",
                              data=request, **options)

        return Response.from_rpc_response(target_, request, response.json())

    def shutdown(self):
        """shutdown the underlying httpx session"""
        self._session.close()
