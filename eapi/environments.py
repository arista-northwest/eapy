# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
import os

from eapi.types import Timeout

# Specifies the default result encoding.  The alternative is 'text'
EAPI_DEFAULT_ENCODING: str = os.environ.get("EAPI_DEFAULT_ENCODING", "json")

# Specifies whether to add timestamps for each command by default
EAPI_INCLUDE_TIMESTAMPS: bool = bool(os.environ.get("EAPI_INCLUDE_TIMESTAMPS", False))

EAPI_DEFAULT_TIMEOUT: Timeout = int(os.environ.get("EAPI_DEFAULT_TIMEOUT", 30.0))

# By default eapi uses HTTP.  HTTPS ('https') is also supported
EAPI_DEFAULT_TRANSPORT: str = os.environ.get("EAPI_DEFAULT_TRANSPORT", "http")

# Set this to false to allow untrusted HTTPS/SSL
SSL_VERIFY: bool = bool(os.environ.get("SSL_VERIFY", True))

# Set this to false to supress warnings about untrusted HTTPS/SSL
SSL_WARNINGS: bool = bool(os.environ.get("SSL_WARNINGS", True))