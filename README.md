



# SuperKabuki
# SCTE-35 Inserter
# SCTE-35 Ad Insertion 
# SCTE-35 Packet Injection for MPEGTS.
#### Latest Version is `v.0.0.63` Released `Wed Jun  5 08:50:29 PM EDT 2024`



## Install
```js

python3 -mpip install superkabuki
```
## Cli Options
```js
a@debian:~/SuperKabuki$ superkabuki -h

usage: superkabuki [-h] [-i INPUT] [-o OUTPUT] [-s SIDECAR] [-p SCTE35_PID] [-t] [-v]

options:
  -h, --help            show this help message and exit
  
  -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or "udp://@235.35.3.5:3535" or
                        "https://futzu.com/xaa.ts" (default sys.stdin.buffer)
                        
  -o OUTPUT, --output OUTPUT
                        Output file (default sys.stdout.buffer)
                        
  -s SIDECAR, --sidecar SIDECAR
                        Sidecar file for SCTE35 (default sidecar.txt)
                        
  -p SCTE35_PID, --scte35_pid SCTE35_PID
                        Pid for SCTE-35 packets, can be hex or integer. (default 0x86)
                        
  -t, --time_signals    Flag to insert Time Signal cues at iframes.
  
  -v, --version         Show version


```

 * Use Superkabuki to insert time signal cues at every iframe.

 ```js
 superkabuki -i your_video.ts -o output.ts -t -p 0x197
 ```
 * verify with threefive ( _installs with superkabuki_ )
 ```js

threefive output.ts
```

 
## Sidecar Files
* Load scte35 cues from a Sidecar file.
 
 ```js
a@debian:~/x9k3$ cat sidecar.txt

38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ== 
38199.918911, /DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0= 
```

* line format for sidecar file is __insert_pts, cue__ ,
     * like `38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==`

* pts is the insert time for the cue, cue can be base64,hex, int, or bytes.

* The __insert_pts has to be valid for the video__, meaning if your insert_pts is 38103.868589, the video PTS has to be 
less than 38103.868589 for the cue to be inserted.


* SuperKabuki with a sidecar file sidecar.txt, and SCTE-35 pid  0x86    
```
superkabuki -i input_file -s sidecar.txt -p 0x86
```
 
## Encoding SCTE-35 Cues
 * [ Two Step SCTE-35 Encoding for MPEGTS](https://github.com/futzu/threefive/blob/master/EasyEncode.md) 

 * [Encoding](https://github.com/futzu/scte35parser-threefive/blob/master/Encoding.md)
 * [Encoding | more ](https://github.com/futzu/scte35parser-threefive/blob/master/EncodingPipeMore.md)

