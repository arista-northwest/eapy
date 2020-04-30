# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import math
import re
import time

from typing import Callable, Iterator, List, Optional

from eapi.types import Auth, Certificate, Command
from eapi.messages import Response
from eapi import Session, AsyncSession

NEVER_RE = r'(?!x)x'


def execute(target: str,
        commands: List[Command],
        encoding: Optional[str] = None,
        auth: Optional[Auth] = None,
        cert: Optional[Certificate] = None,
        verify: Optional[bool] = None,
        **kwargs) -> Response:
    """Send an eAPI request

    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param \*\*kwargs: pass through ``httpx`` options

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    with Session(auth=auth, cert=cert, verify=verify) as sess:
        return sess.send(target, commands, encoding=encoding, **kwargs)


def enable(target: str, commands: List[Command], secret: str = "",
        encoding: Optional[str] = None, **kwargs) -> Response:
    """Prepend 'enable' command
    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param \*\*kwargs: Optional arguments that ``_send`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    commands.insert(0, {"cmd": "enable", "input": secret})
    return execute(target, commands, encoding, **kwargs)


def configure(target: str, commands: List[Command],
        encoding: Optional[str] = None, **kwargs) -> Response:
    """Wrap commands in a 'configure'/'end' block

    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param \*\*kwargs: Optional arguments that ``execute`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    commands.insert(0, "configure")
    commands.append("end")
    return execute(target, commands, encoding, **kwargs)


def watch(target: str,
        command: Command,
        callback: Callable = None,
        encoding: Optional[str] = None,
        interval: Optional[int] = None,
        deadline: Optional[float] = None,
        exclude: bool = False,
        condition: Optional[str] = None,
        **kwargs) -> Optional[Iterator[Response]]:
    
    """Watch a command until deadline or condition matches

    :param target: eAPI target 
    :param type: Target
    :param commmand: A single command to send
    :param type: list
    :param callback: Callback function for responses
    :param type: Callable
    :param encoding: json or text (default: json)
    :param type: str
    :param interval: time between repeating command
    :param type: int
    :param deadline: End loop after specified time
    :param type: float
    :param exclude: return if condition patter is NOT matched
    :param type: bool
    :param condition: search for pattern in output, return if matched
    :param type: str

    :param \*\*kwargs: Optional arguments that ``execute`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """
    
    matched: bool = False

    exclude = bool(exclude)

    if not interval:
        interval = 2

    if not deadline:
        deadline = math.inf

    if not condition:
        condition = NEVER_RE

    start = time.time()
    check = start

    while (check - deadline) < start:
        response = execute(target, [command], encoding, **kwargs)
        match = re.search(condition, str(response))

        if exclude and not match:
            matched = True
        elif match:
            matched = True
        
        callback(response, matched)

        if matched:
            break

        time.sleep(interval)
        check = time.time()

async def aexecute(target: str,
        commands: List[Command],
        encoding: Optional[str] = None,
        auth: Optional[Auth] = None,
        cert: Optional[Certificate] = None,
        verify: Optional[bool] = None,
        **kwargs) -> Response:
    """Send command(s) to an eAPI target (async version)

    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param \*\*kwargs: pass through ``httpx`` options

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    async with AsyncSession(auth=auth, cert=cert, verify=verify) as sess:
        return await sess.send(target, commands, encoding=encoding, **kwargs)

async def aenable(target: str, commands: List[Command], secret: str = "",
        encoding: Optional[str] = None, **kwargs) -> Response:
    """Prepend 'enable' command (async version)
    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param \*\*kwargs: Optional arguments that ``_send`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    commands.insert(0, {"cmd": "enable", "input": secret})
    return await aexecute(target, commands, encoding, **kwargs)


async def aconfigure(target: str, commands: List[Command],
        encoding: Optional[str] = None, **kwargs) -> Response:
    """Wrap commands in a 'configure'/'end' block (async version)

    :param target: eAPI target 
    :param type: Target
    :param commmands: List of commands to send to target
    :param type: list
    :param encoding: json or text (default: json)
    :param type: str
    :param \*\*kwargs: Optional arguments that ``execute`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    commands.insert(0, "configure")
    commands.append("end")
    return await aexecute(target, commands, encoding, **kwargs)

async def awatch(target: str,
        command: Command,
        callback: Callable = None,
        encoding: Optional[str] = None,
        interval: Optional[int] = None,
        deadline: Optional[float] = None,
        exclude: bool = False,
        condition: Optional[str] = None,
        
        **kwargs) -> None:
    
    """Watch a command until deadline or condition matches (async version)

    :param target: eAPI target 
    :param type: Target
    :param commmand: A single command to send
    :param type: list
    :param callback: Callback function for responses
    :param type: Callable
    :param encoding: json or text (default: json)
    :param type: str
    :param interval: time between repeating command
    :param type: int
    :param deadline: End loop after specified time
    :param type: float
    :param exclude: return if condition patter is NOT matched
    :param type: bool
    :param condition: search for pattern in output, return if matched
    :param type: str
    :param \*\*kwargs: Optional arguments that ``execute`` takes.

    :return: :class:`Response <Response>` object
    :rtype: eapi.messages.Response
    """

    matched: bool = False
    
    exclude = bool(exclude)

    if not interval:
        interval = 2

    if not deadline:
        deadline = math.inf

    if not condition:
        condition = NEVER_RE

    start = time.time()
    check = start

    while (check - deadline) < start:
        response = await aexecute(target, [command], encoding, **kwargs)

        match = re.search(condition, str(response))

        if exclude and not match:
            matched = True
        elif match:
            matched = True
        
        callback(response, matched)

        if matched:
            break

        time.sleep(interval)
        check = time.time()