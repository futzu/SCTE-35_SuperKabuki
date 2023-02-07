# SuperKabuki
SCTE-35 Packet Injection


### Requires
* threefive
* new_reader
* iframes

```
python3 -mpip install threefive new_reader iframes

```

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


### Sidecar Files
load scte35 cues from a Sidecar file.

line format for text file insert_pts, cue

pts is the insert time for the cue, A four second preroll is standard. cue can be base64,hex, int, or bytes.

The insert_pts has to be valid for the video, meaning if your insert_pts is 38103.868589, the video PTS has to be 
less than 38103.868589 for the cue to be inserted.

```js
a@debian:~/x9k3$ cat sidecar.txt

38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ== 
38199.918911, /DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0= 
```
    
### Usage 
```
python3 superkabuki.py -i input_file -s sidecar.txt -p 0x86
```
