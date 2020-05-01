# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.


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


class EapiPathNotFoundError(EapiError):
    """authentication has failed"""
    pass


class EapiAuthenticationFailure(EapiError):
    """authentication has failed"""
    pass
