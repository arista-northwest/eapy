# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

__version__ = '0.5.0'

from eapi.session import AUTH, ENCODING, INCLUDE_TIMESTAMPS, SSL_VERIFY, \
                         SSL_WARNINGS, TIMEOUT

from eapi.session import Session, session
from eapi.api import configure, execute, login, logout