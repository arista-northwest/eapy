# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import urllib3
import warnings

from typing import Dict, List, Optional, Union

import httpx
import eapi.environments
from eapi.environments import EAPI_DEFAULT_TIMEOUT
from eapi.util import prepare_request
from eapi.exceptions import EapiAuthenticationFailure, EapiError, \
    EapiPathNotFoundError, EapiTimeoutError
from eapi.types import Auth, Certificate, Command

from eapi.messages import Response, Target


class DisableSslWarnings(object):
    """Context manager to disable then re-enable SSL warnings"""
    #pylint: disable=R0903

    def __init__(self):
        self.category = urllib3.exceptions.InsecureRequestWarning

    def __enter__(self):

        if not eapi.environments.SSL_WARNINGS:
            warnings.simplefilter('ignore', self.category)

    def __exit__(self, *args):
        warnings.simplefilter('default', self.category)

class BaseSession(object):

    def __init__(self, 
            klass: Union[httpx.Client, httpx.AsyncClient],
            auth: Optional[Auth] = None,
            cert: Optional[Certificate] = None,
            verify: Optional[bool] = None,
            **kwargs):
        
        if verify is None:
            verify = eapi.environments.SSL_VERIFY

        # use a httpx Session to manage state
        self._session = klass(
            auth=auth,
            cert=cert,
            headers={"Content-Type": "application/json"},
            verify=verify,
            **kwargs
        )

        # store parameters for future requests
        self._eapi_sessions: Dict[str, dict] = {}

    def _handle_send_response(self, response):

        if response.status_code == 401:
            raise EapiAuthenticationFailure(response.reason_phrase)
        
        if response.status_code == 404:
            raise EapiPathNotFoundError(response.reason_phrase)
        
        response.raise_for_status()
        

    def _handle_login_response(self, target, auth, resp):
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

        options = {}
        if not self.logged_in(target):
            # store auth if login fails (without throwing an exception)
            options["auth"] = auth

        self._eapi_sessions[target.domain] = options

    def logged_in(self, 
            target: Union[str, Target],
            transport: Optional[str] = None
        ) -> bool:
        """determines if session cookie is set"""
        target_: Target = Target.from_string(target)

        cookie = self._session.cookies.get("Session", domain=target_.domain)

        return True if cookie else False

class Session(BaseSession):
    def __init__(self,
            auth: Optional[Auth] = None,
            cert: Optional[Certificate] = None,
            verify: Optional[bool] = None,
            **kwargs):

        super().__init__(
            klass=httpx.Client,
            auth=auth,
            cert=cert,
            verify=verify,
            **kwargs
        )

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *args) -> None:
        self.shutdown()

    def _send(self, url, data, **options) -> httpx.Response:
        """Sends the request to EAPI"""

        response = None

        if "timeout" not in options:
            options["timeout"] = eapi.environments.EAPI_DEFAULT_TIMEOUT

        try:
            with DisableSslWarnings():
                response = self._session.post(url, data=json.dumps(data),
                                              **options)
        except urllib3.exceptions.ReadTimeoutError as exc:
            raise EapiTimeoutError(str(exc))
        except httpx.HTTPError as exc:
            raise EapiError(str(exc))

        self._handle_send_response(response)

        return response

    def logout(self, target: Union[str, Target]) -> None:
        """Log out of an eAPI session

        :param target: eAPI target (host, port)
        :param type: Target

        """

        target_: Target = Target.from_string(target)
        
        if target_.domain in self._eapi_sessions:
            del self._eapi_sessions[target_.domain]

        if self.logged_in(target):
            self._send(target_.url + "/logout", data={})

    def login(self, target: Union[str, Target], auth: Optional[Auth] = None) -> None:
        """Login to an eAPI session

        :param target: eAPI target (host, port)
        :param type: Target
        :param auth: username, password tuple
        :param type: Auth
        """
        target_: Target = Target.from_string(target)

        if self.logged_in(target):
            return

        username, password = auth or self._session.auth
        payload = {"username": username, "password": password}

        resp = self._send(target_.url + "/login", data=payload)

        self._handle_login_response(target_, auth, resp)

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
        options = self._eapi_sessions.get(target_.domain) or {}
        options.update(kwargs)
        
        request = prepare_request(commands, encoding)

        response = self._send(target_.url + "/command-api",
                              data=request, **options)

        return Response.from_rpc_response(target_, request, response.json())

    def shutdown(self):
        """shutdown the underlying httpx session"""
        self._session.close()


class AsyncSession(BaseSession):
    def __init__(self,
            auth: Optional[Auth] = None,
            cert: Optional[Certificate] = None,
            verify: Optional[bool] = None,
            **kwargs):

        super().__init__(
            klass=httpx.AsyncClient,
            auth=auth,
            cert=cert,
            verify=verify,
            **kwargs
        )

    async def aclose(self) -> None:
        await self._session.aclose()
    
    async def __aenter__(self) -> "AsyncSession":
        return self

    async def __aexit__(self, *args) -> None:
        await self.aclose()

    async def _send(self, url, data, **options) -> httpx.Response:
        """Sends the request to EAPI"""

        response = None

        if "timeout" not in options:
            options["timeout"] = eapi.environments.EAPI_DEFAULT_TIMEOUT

        try:
            with DisableSslWarnings():
                response = await self._session.post(url, data=json.dumps(data),
                                              **options)
        except urllib3.exceptions.ReadTimeoutError as exc:
            raise EapiTimeoutError(str(exc))
        except httpx.HTTPError as exc:
            raise EapiError(str(exc))
        
        self._handle_send_response(response)

        return response

    async def login(self, target: Union[str, Target], auth: Optional[Auth] = None) -> None:
        """Login to an eAPI session

        :param target: eAPI target (host, port)
        :param type: Target
        :param auth: username, password tuple
        :param type: Auth
        :param \*\*options: other pass through `httpx` options
        :param type: HttpxOptions

        """
        target_: Target = Target.from_string(target)

        if self.logged_in(target):
            return

        username, password = auth or self._session.auth
        payload = {"username": username, "password": password}

        resp = await self._send(target_.url + "/login", data=payload)

        self._handle_login_response(target_, auth, resp)

    async def logout(self, target: Union[str, Target]) -> None:
        """Log out of an eAPI session

        :param target: eAPI target (host, port)
        :param type: Target

        """

        target_: Target = Target.from_string(target)
        
        if target_.domain in self._eapi_sessions:
            del self._eapi_sessions[target_.domain]

        if self.logged_in(target):
            await self._send(target_.url + "/logout", data={})


    async def send(self, target: Union[str, Target], commands: List[Command],
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
        options = self._eapi_sessions.get(target_.domain) or {}
        options.update(kwargs)

        request = prepare_request(commands, encoding)

        response = await self._send(target_.url + "/command-api",
                              data=request, **options)

        return Response.from_rpc_response(target_, request, response.json())