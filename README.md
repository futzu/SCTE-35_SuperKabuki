# SuperKabuki
SCTE-35 Packet Injection for MPEGTS.
# SuperKabuki v.0.0.51 released march 3 2024



<details> <summary>Fast Start </summary>

* Install SuperKabuki
```js

python3 -mpip install superkabuki
```
 * Use Superkabuki to insert time signal cues at every iframe.

 ```js
 superkabuki -i your_video.ts -o output.ts -t
 ```
 * verify with threefive ( _installs with superkabuki_ )
 ```js

threefive output.ts
```

 
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
</details>

<details> <summary>Sidecar Files?</summary>
 
Load scte35 cues from a Sidecar file.
 
 ```js
a@debian:~/x9k3$ cat sidecar.txt

38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ== 
38199.918911, /DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0= 
```

line format for sidecar file __insert_pts, cue__ , like `38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==`

pts is the insert time for the cue, cue can be base64,hex, int, or bytes.

The __insert_pts has to be valid for the video__, meaning if your insert_pts is 38103.868589, the video PTS has to be 
less than 38103.868589 for the cue to be inserted.


    
### Usage 
```
superkabuki -i input_file -s sidecar.txt -p 0x86
```
 
</details>

 
 <details> <summary>Easy SCTE-35 Cue Encoding. </summary>  
 
 
 #### Use threefive.encode helper functions `mk_splice_null` , `mk_splice_insert`, `and mk_time_signal` 
 
```js

>>>> from threefive.encode import mk_splice_null, mk_splice_insert, mk_time_signal
 
>>>> null_cue = mk_splice_null()
>>>> null_cue.show()
{
    "info_section": {
        "table_id": "0xfc",
        "section_syntax_indicator": false,
        "private": false,
        "sap_type": "0x3",
        "sap_details": "No Sap Type",
        "section_length": 17,
        "protocol_version": 0,
        "encrypted_packet": false,
        "encryption_algorithm": 0,
        "pts_adjustment_ticks": 0,
        "cw_index": "0x0",
        "tier": "0xfff",
        "splice_command_length": 0,
        "splice_command_type": 0,
        "descriptor_loop_length": 0,
        "crc": "0x7a4fbfff"
    },
    "command": {
        "command_length": 0,
        "command_type": 0,
        "name": "Splice Null"
    },
    "descriptors": []
}
```
 *  Cue as base64
 ```js
 >>>> b64null = null_cue.encode()
>>>> b64null
'/DARAAAAAAAAAP/wAAAAAHpPv/8='
 ```
 * Cue as hex
 ```js
>>>> hex_null = null_cue.encode_as_hex()
>>>> hex_null
'0xfc301100000000000000fff0000000007a4fbfff'
```
 * Cue as int
 ```js
>>>> int_null = null_cue.encode_as_int()
>>>> int_null
1439737590925997869941740172919141471333225840639
 ```

 ### help(threefive.encode)
 ```js
 
NAME
    threefive.encode - encode.py

DESCRIPTION
    threefive.encode has helper functions for Cue encoding.

FUNCTIONS
    mk_splice_insert(event_id, pts=None, duration=None, out=False)
        mk_cue returns a Cue with a Splice Insert.
        
        The args set the SpliceInsert vars.
        
        splice_event_id = event_id
        
        if pts IS None (default):
            splice_immediate_flag      True
            time_specified_flag        False
        
        if pts IS set:
            splice_immediate_flag      False
            time_specified_flag        True
            pts_time                   pts
        
        If duration IS None (default)
            duration_flag              False
        
        if duration IS set:
            out_of_network_indicator   True
            duration_flag              True
            break_auto_return          True
            pts_time                   pts
        
        if out IS True:
            out_of_network_indicator   True
        
        if out IS False (default):
            out_of_network_indicator   False
    
    mk_splice_null()
        mk_splice_null returns a Cue
        with a Splice Null
    
    mk_time_signal(pts=None)
         mk_time_signal returns a Cue
         with a Time Signal
        
         if pts IS None:
             time_specified_flag   False
        
        if pts IS set:
             time_specified_flag   True
             pts_time              pts

FILE
    /home/a/build/clean/scte35-threefive/threefive/encode.py

```
 
           
 </details>

 
 <details> <summary>Advanced SCTE-35 Cue Encoding. </summary>  


* [SCTE35 Cue with a Time Signal Command in Seven Steps](https://github.com/futzu/scte35-threefive/blob/master/Encoding.md#scte35-cue-with-a-time-signal-command-in-seven-steps) 

* [Edit A Splice Insert Command in a SCTE35 Cue](https://github.com/futzu/scte35-threefive/blob/master/Encoding.md#edit-a-splice-insert-command-in-a--scte35-cue)

* [Remove a Splice Descriptor from a SCTE35 Cue](https://github.com/futzu/scte35-threefive/blob/master/Encoding.md#remove-a-splice-descriptor-from-a-scte35-cue)

* [Add a Dtmf Descriptor to an existing SCTE35 Cue](https://github.com/futzu/scte35-threefive/blob/master/Encoding.md#add-a-dtmf-descriptor-to-an-existing--scte35-cue)


  </details> 





