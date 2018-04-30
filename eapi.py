# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
"""Simple EAPI Client"""

from __future__ import print_function

import json
import uuid
import warnings
import requests
import urllib3

__version__ = "0.2.1"

# Default behaviors
#
# Override example (suppress SSL errors and warnings):
#
# import eapi
# eapi.DEFAULT_TRANSPORT = "https"
# eapi.SSL_VERIFY = False
# eapi.SSL_WARNINGS = False

# See: http://docs.python-requests.org/en/master/user/advanced/#timeouts
CONNECT_TIMEOUT = 5
# AKA: 'read timeout'
EXECUTE_TIMEOUT = 30

# By default eapi uses HTTP.  HTTPS ()'https') is also supported
DEFAULT_TRANSPORT = "http"

# The default username password for all Aristas is 'admin' with no password
DEFAULT_AUTH = ("admin", "")

# Specifies the default output encoding.  The alternative is 'text'
DEFAULT_ENCODING = "json"

# Specifies whether to add timestamps for each command by default
INCLUDE_TIMESTAMPS = False

# This should not need to change.  All responses are JSON
SESSION_HEADERS = {"Content-Type": "application/json"}

# Set this to false to allow untrusted HTTPS/SSL
SSL_VERIFY = True

# Set this to false to supress warnings about untrusted HTTPS/SSL
SSL_WARNINGS = True

class EapiError(Exception):
    """General eAPI failure"""
    pass

class EapiTimeoutError(EapiError):
    """Raise for connect or read timeouts"""
    pass

class EapiHttpError(EapiError):
    """Raised when HTTP code is not 2xx"""
    pass

class EapiResponseError(EapiError):
    """The response contains errors"""
    pass

class EapiAuthenticationFailure(EapiError):
    """authentication has failed"""
    pass


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

class Response(object):
    """Data structure for EAPI responses"""

    def __init__(self, session, commands, output, code=0, message=None):

        # parent session object
        self.session = session

        # status code != 0 signifies an error occured
        self.code = code

        # error message if present
        self.message = message

        # list of responses
        self.output = output

        # original list of commands
        self.commands = commands

    @property
    def errored(self):
        """determine the errored status"""
        return True if self.code != 0 else False

    def to_dict(self):
        """return the response as a dictionary"""
        return {
            "code": self.code,
            "commands": self.commands,
            "message": self.message,
            "output": self.output
        }

    def raise_for_error(self):
        """trigger an exception if response is errored"""
        if self.errored:
            raise EapiResponseError((self.code, self.message))

class Session(object):
    """EAPI Session"""
    #pylint: disable=R0913,R0902

    def __init__(self, hostaddr,
                 auth=DEFAULT_AUTH,
                 cert=None,
                 port=None,
                 timeout=(CONNECT_TIMEOUT, EXECUTE_TIMEOUT),
                 transport=DEFAULT_TRANSPORT,
                 verify=SSL_VERIFY):

        # use a requests Session to manage state
        self._session = requests.Session()

        # every request should send the same headers
        self._session.headers = SESSION_HEADERS

        # host name or IP address
        self.hostaddr = hostaddr

        # authenication tuple containing (username, password)
        self.auth = auth

        # client certificate/key pair as a tuple
        self.cert = cert

        # port is None for default
        self.port = port

        # http or https
        self.transport = transport

        # timeout value in seconds. can also be specified as a (connect, read)
        # tuple
        self.timeout = timeout

        # specifies whether to verify SSL certificate. Can also be set globally
        # with eapi.SSL_VERIFY
        self.verify = verify

    def __enter__(self):
        if not self.cert:
            self.login()
        return self

    def __exit__(self, *args):
        self.logout()
        self.close()

    @property
    def logged_in(self):
        """determines if session cookie is set"""
        if "Session" in self._session.cookies:
            return True
        return False

    def prepare_url(self, path=""):
        """construct the url from path and transport"""
        url = "{}://{}".format(self.transport, self.hostaddr)

        if self.port:
            url += ":{}".format(self.port)

        return url + path

    def close(self):
        """shutdown the session"""
        self._session.close()

    def login(self, **kwargs):
        """Session based authentication"""

        if not len(self.auth) == 2:
            raise ValueError("username and password auth tuple is required")

        username, password = self.auth

        payload = {"username": username, "password": password}
        resp = self._send("/login", data=payload, **kwargs)

        if resp.status_code == 401:
            raise EapiAuthenticationFailure(resp.text)
        elif resp.status_code == 404 or "Session" not in resp.cookies:
            # fall back to basic auth if /login is not found or Session key is
            # missing
            self.auth = (username, password)
            return
        elif resp.cookies["Session"] == "None":
            # this is weird... investigate further
            raise EapiError("Got cookie Session='None' in response")
        elif not resp.ok:
            raise EapiError(resp.reason)

        # set auth to none after successful login. it is no longer required for
        # each request
        self.auth = None

    def logout(self, **kwargs):
        """destroys the session"""
        if self.logged_in:
            self._send("/logout", data={}, **kwargs)

        self.close()

    def execute(self, commands, encoding=DEFAULT_ENCODING,
                timestamps=INCLUDE_TIMESTAMPS, **kwargs):
        """Send commands to switch"""
        code = 0
        message = None
        output = []
        request_id = str(uuid.uuid4())

        params = {
            "version": 1,
            "cmds": commands,
            "format": encoding
        }

        # timestamps is a newer param, only include it if requested
        if timestamps:
            params["timestamps"] = timestamps

        payload = {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": params,
            "id": request_id
        }

        resp = self._send("/command-api", data=payload, **kwargs)

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise EapiHttpError(str(exc))
        resp = resp.json()

        # normalize the errored and clean responses
        if "error" in resp:
            errored = resp["error"]
            code = errored["code"]
            output = errored.get("data")
            message = errored["message"]
        else:
            output = resp["result"]

        return Response(commands, output, code, message)

    # alais for execute to match '/command-api' path
    command_api = execute

    def _send(self, path, data, **kwargs):
        """Sends the request to EAPI"""

        url = self.prepare_url(path)

        kwargs.setdefault("timeout", self.timeout)

        if self.cert:
            kwargs.setdefault("cert", self.cert)

        elif not self.logged_in:
            # Note: if the Session key is in cookies no auth parameter is
            # required.
            kwargs.setdefault("auth", self.auth)

        if self.verify is not None:
            kwargs.setdefault("verify", self.verify)

        try:
            with DisableSslWarnings():
                response = self._session.post(url, data=json.dumps(data),
                                              **kwargs)
        except requests.Timeout as exc:
            raise EapiTimeoutError(str(exc))
        except requests.ConnectionError as exc:
            raise EapiError(str(exc))

        return response

def session(*args, **kwargs):
    """Helper function for new session"""
    return Session(*args, **kwargs)
