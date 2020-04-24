# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
import re
from pprint import pformat
from collections import namedtuple
from collections.abc import Mapping
from typing import List, Union, Optional, Tuple
from typing_extensions import TypedDict

import eapi.sessions
from eapi.structures import Command

from eapi.util import zpad, indent

Error = TypedDict('Error', {
    'code': int,
    'message': str
})


class Target(object):

    _TRANSPORTS = {"http": 80, "https": 443}
    _TARGET_RE = re.compile(
        r"^(?:(?P<transport>\w+)\:\/\/)?(?P<hostname>[\w+\-\.]+)(?:\:(?P<port>\d+))?/*?$")

    def __init__(self, hostname, transport: Optional[str], port: Optional[int]):
        self.hostname = hostname

        if not transport:
            transport = eapi.sessions.TRANSPORT
        elif transport not in self._TRANSPORTS.keys():
            raise ValueError(
                "transport must be 'http' or 'https' not %s" % transport)

        self.transport = transport

        self.port = port or 0

    def __str__(self):
        return self.url

    @property
    def domain(self):
        domain = self.hostname
        if "." not in domain:
            domain += ".local"
        return domain

    @property
    def url(self):
        default_port = self._TRANSPORTS[self.transport]
        url = "%s://%s" % (self.transport, self.hostname)

        if self.port > 0 and self.port != default_port:
            url += ":%d" % self.port

        return url

    @classmethod
    def from_string(cls, target: Union[str, 'Target']):
        if isinstance(target, Target):
            return target

        match = cls._TARGET_RE.search(target)

        if not match:
            raise ValueError("Invalid target: %s" % target)

        transport = match.group("transport")
        hostname = match.group("hostname")

        port = match.group("port")
        port = int(port) if port else None

        return cls(hostname, transport, port)


class TextResult(object):
    def __init__(self, result: str):
        self._data = result.strip()

    def __str__(self):
        return self._data

    @property
    def pretty(self):
        return self._data


class JsonResult(Mapping):
    def __init__(self, result: dict):
        self._data = result

    def __getitem__(self, name):
        return self._data[name]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return str(self._data)

    @property
    def pretty(self):
        return pformat(self._data)


class ResponseElem(object):
    def __init__(self, command: Command, result: Union[TextResult, JsonResult]):
        self._command = command

        if isinstance(self._command, str):
            self.command = self._command
        else:
            self.command = self._command["cmd"]
            self.input = self._command["input"]

        self.result = result

    def to_dict(self):
        if isinstance(self.result, JsonResult):
            result = dict(self.result)
        else:
            result = str(self.result)

        return {
            "command": self.command,
            "input": self.input,
            "result": result
        }

    def __str__(self):
        return str(self.result)


class Response(object):

    def __init__(self, target, elements: List[ResponseElem], error: Error = None):
        self._target = target
        self.elements = elements
        self.error = error

    def __contains__(self, name):
        return name in self.__str__()

    def __iter__(self):
        return iter(self.elements)

    @property
    def code(self):
        return self.error.get("code", 0)

    @property
    def message(self):
        return self.error.get("message", "OK")

    @property
    def target(self):
        return self._target

    def to_dict(self) -> dict:
        out = {}
        out["target"] = self._target
        out["status"] = [self.code, self.message]

        out["responses"] = []
        for elem in self.elements:
            out["responses"].append(elem.to_dict())

        return out

    def __str__(self):
        text = "target: %s\n" % self.target
        text += "status: [%d, %s]\n\n" % (self.code, self.message or "OK")

        text += "responses:\n"

        for elem in self.elements:
            text += "- command: %s\n" % elem.command
            text += "  result: |\n"
            text += indent("    ", elem.result.pretty)
            text += "\n"
        return text

    @classmethod
    def from_rpc_response(cls, target, request, response):

        encoding = request["params"]["format"]
        commands = request["params"]["cmds"]

        error: Error = {"code": 0, "message": ""}

        code: int = 0
        message: str = ""

        errored = response.get("error")
        results = []

        if errored:
            # dump the errored output
            results = errored["data"]
            code = errored["code"]
            message = errored["message"]
            error = {"code": code, "message": message}
        else:
            results = response["result"]

        elements = []
        for cmd, res in zpad(commands, results, {}):
            if encoding == "text":
                res = TextResult(res.get("output", ""))
            else:
                res = JsonResult(res)
            elem = ResponseElem(cmd, res)
            elements.append(elem)

        return cls(target, elements, error)
