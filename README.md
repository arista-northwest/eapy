EAPI-PY: Simple EAPI library
============================

Features:
---------

- SSL Client certificates
- Login/Logout endpoints

Installation
------------

```
pip3 install eapi-py
```

Development
-----------

```
git clone https://gitlab.aristanetworks.com/arista-northwest/eapi-py.git
# installs pipenv and requirements
make init
pipenv shell
```

Usage
-----

### Simple example (uses default username/password):

```python
>>> import eapi
>>> resp = eapi.execute("veos", ["show version"], auth=("admin", "password"), encoding="text")
>>>
>>> print(resp)
```

```
target: veos
status: [0, OK]

responses:
- command: show hostname
  result: |
    Hostname: veos
    FQDN:     veos
- command: show version
  result: |
    vEOS
    Hardware version:    
    Serial number:       
    System MAC address:  0800.27c2.d715
    
    Software image version: 4.23.2.1F
    Architecture:           x86_64
    Internal build version: 4.23.2.1F-16176869.42321F
    Internal build ID:      d07b13c8-e190-49f8-b0bb-79588cedafca
    
    Uptime:                 0 weeks, 0 days, 2 hours and 32 minutes
    Total memory:           2014500 kB
    Free memory:            689532 kB
```

# Login - to avoid sending password everytime
 
```python
>>> eapi.new("veos3", auth=("admin", ""))
>>> resp = eapi.execute("veos3", ["show version"], encoding="text")
>>> print(resp)
... output omitted ...
```

### Same over HTTPS will fail if certificate is not trusted.

_disabled warnings for this example_

```python
>>> eapi.sessions.SSL_WARNINGS = False
>>> eapi.new("https://veos", auth=("admin", ""), verify=False)
>>>
>>> resp = eapi.execute("https://veos", ["show version"], encoding="text")
...
>>> print(resp)
... output omitted ...
```

### Client certificates

See the eAPI client certificate authentication cheetsheet [here](https://gist.github.com/mathershifter/6a8c894156e3c320a443e575f986d78b).

```python
>>> eapi.sessions.SSL_WARNINGS = False
>>> eapi.new("https://veos", cert=("/path/to/client.crt", "/path/to/client.key"), verify=False)
>>> resp = eapi.execute("https://veos", ["show version"])
```
