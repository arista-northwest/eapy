EAPI-PY: Simple EAPI library
============================

Features:
---------

- SSL Client certificates
- Login/Logout endpoints

Installation
------------

```
pip3 install git+https://github.com/arista-northwest/eapi-py.git
```

Usage
-----

### Simple example:

```python
import eapi
sess = eapi.session(hostaddr)
resp = sess.execute(["show version"])
```

```
{
  'jsonrpc': '2.0',
  'id': 'eb4a94bd-d0f1-478c-b13c-96c7f71e74e2',
  'result': [{'modelName': 'DCS-7504',
    'internalVersion': '4.19.5M-LDPLSR-FX-7565027.4195MLDPLSRFX',
    'systemMacAddress': '00:1c:73:03:13:4f',
    'serialNumber': 'JSH11461143',
    'memTotal': 31583784,
    'bootupTimestamp': 1518741254.57,
    'memFree': 26097728,
    'version': '4.19.5M-LDPLSR-FX',
    'architecture': 'i386',
    'isIntlVersion': False,
    'internalBuildId': '6abaa56e-e8cf-457d-a858-377689ffb025',
    'hardwareRevision': '02.00'
  }]
}
```


### Same over HTTPS will fail if certificate is not trusted.

```python
sess = eapi.session(hostaddr, transport="https")
resp = sess.execute(["show version"])
```

```
...

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/jmather/Projects/eapi-py/eapi.py", line 168, in execute
    resp = self.send("/command-api", data=payload, **kwargs)
  File "/Users/jmather/Projects/eapi-py/eapi.py", line 196, in send
    raise EapiError(str(exc))
eapi.EapiError: HTTPSConnectionPool(host='tg219', port=443): Max retries exceeded with url: /command-api (Caused by SSLError(SSLError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777)'),))
```

### Use _verify=False_ to bypass check

```python
sess = eapi.session(hostaddr, transport="https", verify=False)
resp = sess.execute(["show version"])
```

### Client certificates

```python
sess = eapi.session(hostaddr, transport="https", verify=False,
                    cert=(<certfile>, <keyfile>))
resp = sess.execute(["show version"])
```
