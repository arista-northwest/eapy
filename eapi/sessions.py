# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import urllib3
import warnings

from typing import Dict, List, Optional, Union

import requests

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
    def __init__(self):
        # use a requests Session to manage state
        self._session = requests.Session()

        # every request should send the same headers
        # This should not need to change.  All responses are JSON
        self._session.headers = {"Content-Type": "application/json"}

        # store parameters for future requests
        self._eapi_sessions: Dict[str, dict] = {}

    def logged_in(self, target: Union[str, Target], transport: Optional[str] = None):
        """determines if session cookie is set"""
        target_: Target = Target.from_string(target)

        cookie = self._session.cookies.get("Session", domain=target_.domain)

        return True if cookie else False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown()

    def _login(self, target: Target, auth, **kwargs) -> bool:

        if self.logged_in(target):
            return True

        username, password = auth
        payload = {"username": username, "password": password}

        resp = self._send(target.url + "/login", data=payload, **kwargs)

        if resp.status_code == 404:
            # fall back to basic auth if /login is not found
            return False
        elif not resp.ok:
            raise EapiError(resp.reason)

        if "Session" not in resp.cookies:
            warnings.warn(("Got a good response, but no 'Session' found in "
                           "cookies. Using fallback auth."))
            return False
        elif resp.cookies["Session"] == "None":
            # this is weird... investigate further
            warnings.warn("Got cookie Session='None' in response?! "
                          "Using fallback auth.")
            return False

        return True

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
        # except requests.Timeout as exc:
        #     raise EapiTimeoutError(str(exc))
        except requests.ConnectionError as exc:
            raise EapiError(str(exc))

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if response.status_code == 401:
                raise EapiAuthenticationFailure(str(exc))
            raise EapiHttpError(str(exc))

        return response

    def close(self, target: Union[str, Target]) -> None:
        """Create a new eAPI session

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

    logout = close

    def new(self, target: Union[str, Target], auth: Optional[Auth] = None,
            cert: Optional[Certificate] = None, **kwargs) -> None:
        """Create a new eAPI session

        :param target: eAPI target (host, port)
        :param type: Target
        :param auth: username, password tuple
        :param type: Auth
        :param cert: client certificate or (certificate, key) tuple
        :param type: Certificate
        :param \*\*options: other pass through `requests` options
        :param type: RequestsOptions

        """
        target_: Target = Target.from_string(target)

        if auth:
            if not self._login(target_, auth, **kwargs):
                # store auth if login fails (without throwing anm exception)
                kwargs["auth"] = auth
        elif cert:
            kwargs["cert"] = cert

        self._eapi_sessions[target_.domain] = kwargs

    login = new

    def send(self, target: Union[str, Target], commands: List[Command],
             encoding: str = ENCODING, **kwargs):
        """Send commands to an eAPI target

        :param target: eAPI target (host, port)
        :param type: Target
        :param commands: List of `Command` objects
        :param type: list
        :param encoding: response encoding 'json' or 'text' (default: json)
        :param \*\*kwargs: other pass through `requests` options
        :param type: dict

        """

        target_: Target = Target.from_string(target)

        # get session defaults (set at login)
        _options = self._eapi_sessions.get(target_.domain) or {}

        _options.update(kwargs)
        options = _options

        request = prepare_request(commands, encoding)

        response = self._send(target_.url + "/command-api",
                              data=request, **options)

        return Response.from_rpc_response(target_, request, response.json())

    def shutdown(self):
        """shutdown the underlying requests session"""
        self._session.close()


# session singleton(ish)
session = Session()
