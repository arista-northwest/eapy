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
import eapi
sess = eapi.session("spine1")
resp = sess.execute(["show version"])

#
for resp in eapi.session('<hostaddr>').execute(["show version"]):
    print(resp)
```

```
{
  "modelName": "vEOS",
  "internalVersion": "4.20.5F-8127914.4205F",
  "systemMacAddress": "08:00:27:1a:25:cb",
  "serialNumber": "",
  "memTotal": 2016904,
  "bootupTimestamp": 1533056680.02,
  "memFree": 1319412,
  "version": "4.20.5F",
  "architecture": "i386",
  "isIntlVersion": false,
  "internalBuildId": "4d6b4859-39b5-4581-993b-f84ac0736664",
  "hardwareRevision": ""
}
```

### Specify username and password

```python
sess = eapi.session(hostaddr, auth=("joe", "j0ep4ss!"))
resp = sess.execute(["show version"])
```


### Same over HTTPS will fail if certificate is not trusted.

```python
sess = eapi.session("spine1", transport="https")
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
eapi.EapiError: HTTPSConnectionPool(host='"spine1"', port=443): Max retries exceeded with url: /command-api (Caused by SSLError(SSLError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777)'),))
```

### Use _verify=False_ to bypass check

```python
# this will also disable warnings
eapi.SSL_WARNINGS = False
sess = eapi.session("spine1", transport="https", verify=False)
resp = sess.execute(["show version"])
```

### Client certificates

See the eAPI client certificate authentication cheetsheet [here](https://gist.github.com/mathershifter/6a8c894156e3c320a443e575f986d78b).

```python
sess = eapi.session("spine1", transport="https", verify=False,
                    cert=("/path/to/client.crt", "/path/to/client.key"))
resp = sess.execute(["show version"])
```
