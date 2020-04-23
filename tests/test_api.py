# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import eapi

eapi.SSL_WARNINGS = False

def test_session():
    eapi.Session()

def test_login(target, auth):
    eapi.login(target, auth)

def test_execute(target ,commands):
    response = eapi.execute(target, commands=commands)
    print()
    print()
    print(response)

def test_execute_text(target, commands):
    response = eapi.execute(target, commands=commands, encoding="text")

    print()
    print()
    print(response)

def test_execute_jsonerr(target):
    
    response = eapi.execute(target, commands=["show hostname", "show bogus"], encoding="json")
    assert response.code > 0
    
    print()
    print()
    print(response)



def test_execute_err(target):
    
    response = eapi.execute(target, commands=["show hostname", "show bogus", "show running-config"], encoding="text")
    assert response.code > 0
    
    print()
    print()
    print(response)

def test_configure(target):

    eapi.configure(target, [
       "ip access-list standard DELETE_ME",
       "permit any"
    ])

    eapi.execute(target, ["show ip access-list DELETE_ME"])

    eapi.configure(target, [
       "no ip access-list DELETE_ME"
    ])

def test_logout(target):
    eapi.logout(target)