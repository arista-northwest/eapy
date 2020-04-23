# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
from typing import List, NoReturn

from eapi.structures import Target, Auth, Command
from eapi.messages import Response
from eapi import session

def login(target, auth: Auth, **kwargs) -> None:
    """Create an eAPI session

    :param target: eAPI target 
    :param type: Target
    :param auth: username, password tuple
    :param type: Auth
    :param transport: http or https (default: http)
    :param type: str
    :param options: pass through `requests` options
    :param type: RequestsOptions
    """
    session.login(target, auth=auth, **kwargs)

def logout(target: Target, **kwargs):
    """End an eAPI session

    :param target: eAPI target 
    :param type: Target
    :param transport: http or https (default: http)
    :param type: str
    :param options: pass through `requests` options
    :param type: RequestsOptions
    """
    session.logout(target, **kwargs)

def execute(target: Target, commands: List[Command], **kwargs) -> Response:
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
    :param options: pass through `requests` options
    :param type: RequestsOptions

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    response = session.send(target, commands, **kwargs)

    return response

def enable(target: Target, commands: List[Command], secret: str = "",
        **kwargs) -> Response:
    r"""Prepend 'enable' command
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


def configure(target: Target, commands: List[Command], **kwargs) -> Response:
    r"""Wrap commands in a 'configure'/'end' block
    
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