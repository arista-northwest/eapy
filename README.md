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
>>> resp = eapi.execute("veos", ["show version"], encoding="text",
...    options={"auth": ("admin", "password")})
...
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
>>> eapi.login("veos3", ("admin", ""))
>>> resp = eapi.execute("veos3", ["show version"], encoding="text")
>>> print(resp)
... output omitted ...
```

### Same over HTTPS will fail if certificate is not trusted.

_disabled warnings for this example_

```python
>>> eapi.session.SSL_WARNINGS = False
>>> eapi.login("veos", ("admin", ""), transport="https", , options={
...   verify=False
... })
...
>>> resp = eapi.execute("veos", ["show version"], transport="https", encoding="text", options={
...   verify=False
... })
...
>>> print(resp)
... output omitted ...
```

### Client certificates

See the eAPI client certificate authentication cheetsheet [here](https://gist.github.com/mathershifter/6a8c894156e3c320a443e575f986d78b).

```python
sess = eapi.execute("host", transport="https", verify=False, options={
  "cert": ("/path/to/client.crt", "/path/to/client.key"),
  "verify": False
})
```
