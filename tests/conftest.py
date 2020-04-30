
import os
import sys
import re
import pytest

sys.path.insert(0, os.path.abspath("."))

import eapi.sessions

from eapi.sessions import Session

from eapi.messages import _TARGET_RE
from eapi.structures import Certificate, Request
from eapi.util import prepare_request

EAPI_TARGET = os.environ.get('EAPI_TARGET', "")
EAPI_STARGET = os.environ.get('EAPI_STARGET', "")
EAPI_USER = os.environ.get('EAPI_USER', "admin")
EAPI_PASSWORD = os.environ.get('EAPI_PASSWORD', "")
EAPI_CLIENT_CERT = os.environ.get('EAPI_CLIENT_CERT')
EAPI_CLIENT_KEY = os.environ.get('EAPI_CLIENT_KEY')

eapi.sessions.SSL_WARNINGS = False


@pytest.fixture
def auth():
    return (EAPI_USER, EAPI_PASSWORD)

@pytest.fixture
def cert():
    cert: Certificate = None

    if EAPI_CLIENT_CERT:
        if not EAPI_CLIENT_KEY:
            cert = EAPI_CLIENT_CERT
        else:
            cert = (EAPI_CLIENT_CERT, EAPI_CLIENT_KEY)
    
    return cert

@pytest.fixture
def session(cert, auth):
    return Session(auth=auth, cert=cert, verify=False)

@pytest.fixture
def target():
    return EAPI_TARGET

@pytest.fixture
def starget(target):
    port = None
    
    if EAPI_STARGET:
        _, hostname, port = _TARGET_RE.match(EAPI_STARGET).groups()
    else:
        _, hostname, _ = _TARGET_RE.match(target).groups()
    
    starget = "https://%s" % hostname
    if port:
       starget += ":%d" % int(port) 
    
    return starget


@pytest.fixture()
def commands():
    return ["show hostname", "show version"]

@pytest.fixture(params=["json", "text"])
def reqwest(commands, request) -> Request:
    return prepare_request(commands, request.param)

@pytest.fixture()
def text_response():
    request = prepare_request(["show hostname", "show version"], "text")
    response = {
        'jsonrpc': '2.0',
        'id': '45e8f5f4-7620-43c9-8407-da0a03bbcc50',
        'result': [
            {
                'output': 'Hostname: rbf153\n'
                          'FQDN:     rbf153.sjc.aristanetworks.com\n'
            }, {
                'output': 'Arista DCS-7280CR2M-30-F\n'
                          'Hardware version:    20.01\n'
                          'Serial number:       JAS18140236\n'
                          'System MAC address:  7483.ef02.a6fb\n\n'
                          'Software image version: 4.23.2.1F-DPE\n'
                          'Architecture:           i686\n'
                          'Internal build version: 4.23.2.1F-DPE-16108061.42321F\n'
                          'Internal build ID:      73a5535d-c66e-4597-b6ed-8999e76b66ea\n\n'
                          'Uptime:                 1 weeks, 6 days, 16 hours and 35 minutes\n'
                          'Total memory:           32890040 kB\n'
                          'Free memory:            25851572 kB\n\n'
            }
        ]
    }

    return "localhost", request, response

@pytest.fixture()
def json_response():
    request = prepare_request(["show hostname", "show version"], "json")
    response = {
        'jsonrpc': '2.0',
        'id': '532c456f-0b5a-4e20-885b-0e838aa1bb57',
        'result': [
            {
                'fqdn': 'rbf153.sjc.aristanetworks.com',
                'hostname': 'rbf153'
            }, {
                'memTotal': 32890040, 
                'uptime': 1181670.77, 
                'modelName': 'DCS-7280CR2M-30-F',
                'internalVersion': '4.23.2.1F-DPE-16108061.42321F',
                'mfgName': 'Arista',
                'serialNumber': 'JAS18140236',
                'systemMacAddress':'74:83:ef:02:a6:fb',
                'bootupTimestamp': 1586324536.0,
                'memFree': 25852932,
                'version': '4.23.2.1F-DPE',
                'architecture': 'i686',
                'isIntlVersion': False,
                'internalBuildId': '73a5535d-c66e-4597-b6ed-8999e76b66ea',
                'hardwareRevision': '20.01'
            }
        ]
    }

    return "localhost", request, response

@pytest.fixture()
def errored_response():
    request = prepare_request(["show hostname", "show bogus"], "json")
    response = {
        'jsonrpc': '2.0',
        'id': '6585432e-2214-43d8-be6b-06bf68617aba',
        'error': {
            'data': [
                {
                    'fqdn': 'veos3-782f',
                    'hostname': 'veos3-782f'
                }, {
                    'errors': [
                        "Invalid input (at token 1: 'bogus')"
                    ]
                }
            ],
            
            'message': "CLI command 2 of 2 'show bogus' failed: invalid command",
            'code': 1002
        }
    }

    return "localhost", request, response 

@pytest.fixture()
def errored_text_response():
    request = prepare_request(["show hostname", "show bogus"], "text")
    response = {
        'jsonrpc': '2.0',
        'id': '072cdc16-be82-4f98-9c42-549a954b5881',
        'error': {
            'data': [
                {
                    'output': 'Hostname: veos3-782f\n'
                              'FQDN:     veos3-782f\n'
                }, {
                    'output': "% Invalid input (at token 1: 'bogus')\n",
                    'errors': ["Invalid input (at token 1: 'bogus')"]
                }
            ],
            'message': "CLI command 2 of 2 'show bogus' failed: invalid command",
            'code': 1002
        }
    }

    return "localhost", request, response

@pytest.fixture()
def jsonrpcerr_response():
    response = {
        'jsonrpc': '2.0',
        'id': None,
        'error': {
            'message': "Expected field 'jsonrpc' not specified", 
            'code': -32600
        }
    }

    return "localhost", None, response