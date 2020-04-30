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

### CLI

```bash
% eapi --help
Usage: eapi [OPTIONS] TARGET COMMAND [ARGS]...

Options:
  -u, --username TEXT     Username (default: admin
  -p, --password TEXT     Username (default: <blank>
  --cert TEXT             Client certificate file
  --key TEXT              Private key file name
  --verify / --no-verify  verify SSL cert
  --help                  Show this message and exit.

Commands:
  execute
  watch

% eapi veos execute "show version"
target: http://veos3
status: [0, OK]

responses:
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

    Uptime:                 0 weeks, 0 days, 2 hours and 21 minutes
    Total memory:           2014500 kB
    Free memory:            616500 kB

% eapi veos watch "show clock"
Watching: 'show clock' on http://veos3
Tue Apr 28 18:16:12 2020
Timezone: UTC
Clock source: local
^C
Aborted!
```

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

### Watch w/ callback

```python
import eapi
def _callback(response):
    for intf, stats in response[0].result["interfaces"].items():
        if stats["inBpsRate"] < 1.0 and stats["outBpsRate"] < 1.0:
            continue
        print("%s: %.2f %.2f" % (intf, stats["inBpsRate"], stats["outBpsRate"]))

eapi.watch("switch", "show interfaces counters rates", 
  auth=("admin", ""), callback=_callback)
```

_Output:_

```
Ethernet1/1: 27626716076.31 53265.03
Ethernet18/1: 229200.85 14655845830.05
Ethernet22/1: 86.24 120.63
Port-Channel2: 351170.64 29268271539.15
Ethernet17/1: 137304.38 14643103747.58
Ethernet21/1: 8453.93 8043.44
Management1: 14495.04 24897.54
Port-Channel1: 12685.43 7732.44
Ethernet3/1: 0.00 551.77
Ethernet1/1: 27627041678.14 58635.84
Ethernet18/1: 287323.71 14655830910.19
Ethernet22/1: 70.61 131.78
Port-Channel2: 975137.23 38892350187.13
Ethernet17/1: 157613.59 14643105143.17
Ethernet21/1: 8997.78 8694.72
Management1: 14383.06 24732.90
Port-Channel1: 10769.91 10321.52
Ethernet3/1: 0.00 550.58
```

### Same over HTTPS will fail if certificate is not trusted.

_disabled warnings for this example_

```python
>>> eapi.sessions.SSL_WARNINGS = False
>>> resp = eapi.execute("https://veos", ["show version"], encoding="text", auth=("admin", ""), verify=False)
...
>>> print(resp)
... output omitted ...
```

### Client certificates

See the eAPI client certificate authentication cheetsheet [here](https://gist.github.com/mathershifter/6a8c894156e3c320a443e575f986d78b).

```python
>>> eapi.sessions.SSL_WARNINGS = False
>>> resp = eapi.execute("https://veos", ["show version"], cert=("/path/to/client.crt", "/path/to/client.key"), verify=False)
```
