# SuperKabuki
SCTE-35 Packet Injection

```js
a@debian:~/build/scte35-threefive$ pypy3 superkabuki.py -h
usage: superkabuki.py [-h] [-i INPUT] [-o OUTPUT] [-s SIDECAR] [-p SCTE35_PID]
                      [-v]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or
                        "udp://@235.35.3.5:3535" or "https://futzu.com/xaa.ts"
  -o OUTPUT, --output OUTPUT
                        Output file
  -s SIDECAR, --sidecar SIDECAR
                        Sidecar file for SCTE35
  -p SCTE35_PID, --scte35_pid SCTE35_PID
                        Pid for SCTE-35 packets
  -v, --version         Show version
```
