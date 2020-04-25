# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List, Optional

from eapi.structures import Auth, Certificate, Command
from eapi.messages import Response
from eapi import session


def new(target: str, auth: Optional[Auth] = None,
        cert: Optional[Certificate] = None, **kwargs) -> None:
    """Create an eAPI session

    :param target: eAPI target 
    :param type: Target
    :param auth: username, password tuple
    :param type: Auth
    :param cert: client certificate or (certificate, key) tuple
    :param type: Certificate
    :param \*\*options: pass through `requests` options
    :param type: RequestsOptions
    """
    session.new(target, auth=auth, cert=cert, **kwargs)


login = new


def close(target: str, **kwargs):
    """End an eAPI session

    :param target: eAPI target 
    :param type: Target
    :param transport: http or https (default: http)
    :param type: str
    :param \*\*kwargs: pass through `requests` options
    :param type: RequestsOptions
    """
    session.logout(target, **kwargs)


logout = close


def execute(target: str, commands: List[Command],
            encoding: Optional[str] = None, **kwargs) -> Response:
    """Send an eAPI request

    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param transport: http or https (default: http)
    :param type: str
    :param timestamps: Include command timestamps (default: False)
    :param type: bool
    :param \*\*kwargs: pass through `requests` options
    :param type: RequestsOptions

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    response = session.send(target, commands, **kwargs)

    return response


def enable(target: str, commands: List[Command], secret: str = "",
           **kwargs) -> Response:
    """Prepend 'enable' command
    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param \*\*kwargs: Optional arguments that ``execute`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """
    commands.insert(0, {"cmd": "enable", "input": secret})
    return execute(target, commands=commands, **kwargs)


def configure(target: str, commands: List[Command], **kwargs) -> Response:
    """Wrap commands in a 'configure'/'end' block

    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param \*\*kwargs: Optional arguments that ``session.send`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """
    commands.insert(0, "configure")
    commands.append("end")
    return execute(target, commands=commands, **kwargs)
