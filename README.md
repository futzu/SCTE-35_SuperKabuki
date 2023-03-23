# SuperKabuki
SCTE-35 Packet Injection
# SuperKabuki v.0.0.39 is now Released.
![image](https://user-images.githubusercontent.com/52701496/222034768-b8b1b34c-a645-461c-9408-6fffe2d40d63.png)

### Fast Start

* Insert time signal cues at every iframe

```js

python3 -mpip install superkabuki

 superkabuki -i your_video.ts -o output.ts -t

threefive output.ts
```


### Requires
* threefive
* new_reader
* iframes

```
python3 -mpip install threefive new_reader iframes

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


### Sidecar Files
load scte35 cues from a Sidecar file.

line format for sidecar file __insert_pts, cue__ , like `38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==`

pts is the insert time for the cue, cue can be base64,hex, int, or bytes.

The __insert_pts has to be valid for the video__, meaning if your insert_pts is 38103.868589, the video PTS has to be 
less than 38103.868589 for the cue to be inserted.

```js
a@debian:~/x9k3$ cat sidecar.txt

38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ== 
38199.918911, /DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0= 
```
    
### Usage 
```
superkabuki -i input_file -s sidecar.txt -p 0x86
```




<details> <summary><h1>Cool....but how do I make a SCTE-35 Cue?</h1> </summary>

<details> <summary><h3>Easy SCTE-35 Cue Encoding.</h3> </summary>  
 
 
 #### Use threefive.encode helper functions `mk_splice_null` , `mk_splice_insert`, `and mk_time_signal` 
 
```js

>>>> from threefive.encode import mk_splice_null, mk_splice_insert, \
mk_time_signal
 
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
        
        if pts is None (default):
            splice_immediate_flag      True
            time_specified_flag        False
        
        if pts:
            splice_immediate_flag      False
            time_specified_flag        True
            pts_time                   pts
        
        If duration is None (default)
            duration_flag              False
        
        if duration IS set:
            out_of_network_indicator   True
            duration_flag              True
            break_auto_return          True
            pts_time                   pts
        
        if out is True:
            out_of_network_indicator   True
        
        if out is False (default):
            out_of_network_indicator   False
    
    mk_splice_null()
        mk_splice_null returns a Cue
        with a Splice Null
    
    mk_time_signal(pts=None)
         mk_time_signal returns a Cue
         with a Time Signal
        
         if pts is None:
             time_specified_flag   False
        
        if pts IS set:
             time_specified_flag   True
             pts_time              pts

FILE
    /home/a/build/clean/scte35-threefive/threefive/encode.py

```
 </details>

 <details> <summary><h3>Advanced SCTE-35 Cue Encoding.</h3> </summary>  

   Encoding ( Requires threefive 2.3.02+ )

* [SCTE35 Cue with a Time Signal Command in Seven Steps](#scte35-cue-with-a-time-signal-command-in-seven-steps) 

* [Edit A Splice Insert Command in a SCTE35 Cue](#edit-a-splice-insert-command-in-a--scte35-cue)

* [Remove a Splice Descriptor from a SCTE35 Cue](#remove-a-splice-descriptor-from-a-scte35-cue)

* [Add a Dtmf Descriptor to an existing SCTE35 Cue](#add-a-dtmf-descriptor-to-an-existing--scte35-cue)

#### `Details`

* A decoded __Cue__ instance contains: 

     * **cue.info_section** one [threefive.**SpliceInfoSection()**](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/section.py)

     * **cue.command**  one of the following [ threefive.**BandwidthReservation()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/commands.py#L32), [ threefive.**PrivateCommand()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/commands.py#L54), [ threefive.**SpliceInsert()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/commands.py#L139), [ threefive.**SpliceNull()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/commands.py#L43), [ threefive.**TimeSignal()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/commands.py#L84)

     * **cue.descriptors** a list of 0 or more of the following [ threefive.**AudioDescriptor()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/descriptors.py#L153), 
        [ threefive.**AvailDescriptor()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/descriptors.py#L50),
        [ threefive.**DtmfDescriptor()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/descriptors.py#L78),
        [ threefive.**SegmentationDescriptor()** ](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/descriptors.py#L201),
        [threefive.**TimeDescriptor()**](https://github.com/futzu/SCTE35-threefive/blob/master/threefive/descriptors.py#L119)

* All instance vars can be accessed via dot notation.

* Automatic Features
    * Splice Info Section of the Cue is automatically generated. 
    * length vars for Cue.command and Cue.descriptors are automatically generated.  
    * Descriptor loop length and crc32 are automatically calculated 


## SCTE35 Cue with a Time Signal Command in Seven Steps

```python3
>>>> import threefive
```
1. __Create an empty SCTE-35 Cue__
```smalltalk

>>>> cue = threefive.Cue()
```
2.  __The info_section is automatically generated__
```smalltalk
>>>> cue
{'info_section': {'table_id': None, 'section_syntax_indicator': None, 'private': None, 'sap_type': None, 'sap_details': None, 'section_length': None,
'protocol_version': None, 'encrypted_packet': None, 'encryption_algorithm': None, 'pts_adjustment': None, 'cw_index': None, 'tier': None,
'splice_command_length': None, 'splice_command_type': None, 'descriptor_loop_length': 0, 'crc': None},
'command': None, 
'descriptors': [], 
'packet_data': None}
```
3. __Create a Time Signal Splice Command__
```smalltalk
>>>> cmd=threefive.TimeSignal()
>>>> cmd
{'calculated_length': None, 'command_type': 6, 'name': 'Time Signal', 'bites': None, 'time_specified_flag': None, 'pts_time': None}
```

4. __Edit the Time Signal__ 
```smalltalk
>>>> cmd.time_specified_flag=True
>>>> cmd.pts_time=20.004350
>>>>
```
5. __Add it to the SCTE35 Cue.__
```smalltalk
>>>> cue.command=cmd
>>>> cue
{'info_section': {'table_id': None, 'section_syntax_indicator': None, 'private': None, 'sap_type': None, 'sap_details': None, 'section_length': None,
'protocol_version': None, 'encrypted_packet': None, 'encryption_algorithm': None, 'pts_adjustment': None, 'cw_index': None, 'tier': None,
'splice_command_length': None, 'splice_command_type': None, 'descriptor_loop_length': 0, 'crc': None}, 

'command': {'calculated_length': None, 'command_type': 6, 'name': 'Time Signal', 'bites': None, 'time_specified_flag': True, 'pts_time': 20.00435},
'descriptors': [], 'packet_data': None}
```
6. Encode the SCTE35 Cue
```smalltalk
>>>> cue.encode()
'/DAWAAAAAAAAAP/wBQb+ABt4xwAAwhCGHw=='
```
7. __Show the Cue data.__
```smalltalk
>>>> cue.show()


{
    "info_section": {
        "table_id": "0xfc",
        "section_syntax_indicator": false,
        "private": false,
        "sap_type": "0x3",
        "sap_details": "No Sap Type",
        "section_length": 22,
        "protocol_version": 0,
        "encrypted_packet": false,
        "encryption_algorithm": 0,
        "pts_adjustment": 0.0,
        "cw_index": "0x0",
        "tier": "0xfff",
        "splice_command_length": 5,
        "splice_command_type": 6,
        "descriptor_loop_length": 0,
        "crc": "0xc210861f"
    },
    "command": {
        "command_type": 6,
        "name": "Time Signal",
        "time_specified_flag": true,
        "pts_time": 20.00435,
        "command_length": 5
    },
    "descriptors": []
}
>>>> 


```


### Edit A Splice Insert Command in a  SCTE35 Cue 
```python3
a@fumatica:~/threefive$ pypy3
Python 3.7.10 (7.3.5+dfsg-2, Jun 03 2021, 20:39:46)
[PyPy 7.3.5 with GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>> import threefive
>>>> Base64 = "/DAvAAAAAAAA///wFAVIAACPf+/+c2nALv4AUsz1AAAAAAAKAAhDVUVJAAABNWLbowo="
>>>> cue = threefive.Cue(Base64)
>>>> cue.decode()
True
>>>> cue.command
{'calculated_length': 20, 'command_type': 5, 'name': 'Splice Insert', 'time_specified_flag': True, 'pts_time': 21514.559089, 'break_auto_return': True, 'break_duration': 60.293567, 'splice_event_id': 1207959695, 'splice_event_cancel_indicator': False, 'out_of_network_indicator': True, 'program_splice_flag': True, 'duration_flag': True, 'splice_immediate_flag': False, 'component_count': None, 'components': None, 'unique_program_id': 0, 'avail_num': 0, 'avail_expected': 0}


# Access vars with dot notation

>>>> cue.command.break_duration= 90.0

# re-encode

>>>> cue.encode()
'/DAvAAAAAAAA///wFAVIAACPf+/+c2nALv4Ae5igAAAAAAAKAAhDVUVJAAABNVB2fJs='
>>>> 
>>>> cue.show()
{
    "info_section": {
        "table_id": "0xfc",
        "section_syntax_indicator": false,
        "private": false,
        "sap_type": "0x3",
        "sap_details": "No Sap Type",
        "section_length": 47,
        "protocol_version": 0,
        "encrypted_packet": false,
        "encryption_algorithm": 0,
        "pts_adjustment": 0.0,
        "cw_index": "0xff",
        "tier": "0xfff",
        "splice_command_length": 20,
        "splice_command_type": 5,
        "descriptor_loop_length": 10,
        "crc": "0x62dba30a"
    },
    "command": {
        "calculated_length": 20,
        "command_type": 5,
        "name": "Splice Insert",
        "time_specified_flag": true,
        "pts_time": 21514.559089,
        "break_auto_return": true,
        "break_duration": 90.0,
        "splice_event_id": 1207959695,
        "splice_event_cancel_indicator": false,
        "out_of_network_indicator": true,
        "program_splice_flag": true,
        "duration_flag": true,
        "splice_immediate_flag": false,
        "unique_program_id": 0,
        "avail_num": 0,
        "avail_expected": 0
    },
    "descriptors": [
        {
            "tag": 0,
            "descriptor_length": 8,
            "name": "Avail Descriptor",
            "identifier": "CUEI",
            "provider_avail_id": 309
        }
    ]
}
```
### Remove a Splice Descriptor from a SCTE35 Cue
```python3
>>>> import threefive
>>>> Base64 = "/DAvAAAAAAAA///wFAVIAACPf+/+c2nALv4AUsz1AAAAAAAKAAhDVUVJAAABNWLbowo="
>>>> cue = threefive.Cue(Base64)
>>>> cue.decode()
True
>>>> cue.show()
{
    "info_section": {
        "table_id": "0xfc",
        "section_syntax_indicator": false,
        "private": false,
        "sap_type": "0x3",
        "sap_details": "No Sap Type",
        "section_length": 47,
        "protocol_version": 0,
        "encrypted_packet": false,
        "encryption_algorithm": 0,
        "pts_adjustment": 0.0,
        "cw_index": "0xff",
        "tier": "0xfff",
        "splice_command_length": 20,
        "splice_command_type": 5,
        "descriptor_loop_length": 10,
        "crc": "0x62dba30a"
    },
    "command": {
        "calculated_length": 20,
        "command_type": 5,
        "name": "Splice Insert",
        "time_specified_flag": true,
        "pts_time": 21514.559089,
        "break_auto_return": true,
        "break_duration": 60.293567,
        "splice_event_id": 1207959695,
        "splice_event_cancel_indicator": false,
        "out_of_network_indicator": true,
        "program_splice_flag": true,
        "duration_flag": true,
        "splice_immediate_flag": false,
        "unique_program_id": 0,
        "avail_num": 0,
        "avail_expected": 0
    },
    "descriptors": [
        {
            "tag": 0,
            "descriptor_length": 8,
            "name": "Avail Descriptor",
            "identifier": "CUEI",
            "provider_avail_id": 309
        }
    ]
}

# delete the descriptor from descriptors

>>>> del cue.descriptors[0]

# re-encode 

>>>> cue.encode()
'/DAlAAAAAAAA///wFAVIAACPf+/+c2nALv4AUsz1AAAAAAAAYinJUA=='
>>>> cue.show()
{
    "info_section": {
        "table_id": "0xfc",
        "section_syntax_indicator": false,
        "private": false,
        "sap_type": "0x3",
        "sap_details": "No Sap Type",
        "section_length": 37,
        "protocol_version": 0,
        "encrypted_packet": false,
        "encryption_algorithm": 0,
        "pts_adjustment": 0.0,
        "cw_index": "0xff",
        "tier": "0xfff",
        "splice_command_length": 20,
        "splice_command_type": 5,
        "descriptor_loop_length": 0,
        "crc": "0x6229c950"
    },
    "command": {
        "calculated_length": 20,
        "command_type": 5,
        "name": "Splice Insert",
        "time_specified_flag": true,
        "pts_time": 21514.559089,
        "break_auto_return": true,
        "break_duration": 60.293567,
        "splice_event_id": 1207959695,
        "splice_event_cancel_indicator": false,
        "out_of_network_indicator": true,
        "program_splice_flag": true,
        "duration_flag": true,
        "splice_immediate_flag": false,
        "unique_program_id": 0,
        "avail_num": 0,
        "avail_expected": 0,
        "command_length": 20
    },
    "descriptors": []
}

```
### Add a Dtmf Descriptor to an existing  SCTE35 Cue
```python3
>>>> import threefive
>>>> Base64 = "/DAvAAAAAAAA///wFAVIAACPf+/+c2nALv4AUsz1AAAAAAAKAAhDVUVJAAABNWLbowo="
>>>> cue = threefive.Cue(Base64)
>>>> cue.decode()
True
>>>> dscrptr = threefive.DtmfDescriptor()
>>>> dscrptr
{'tag': 1, 'descriptor_length': 0, 'identifier': None, 'bites': None, 'name': 'DTMF Descriptor', 'preroll': None, 'dtmf_count': None, 'dtmf_chars': []}

 # My data to load into the DtmfDescriptor instance

>>>> data = {'tag': 1, 'descriptor_length': 10, 'identifier': 'CUEI', 'name': 'DTMF Descriptor', 'preroll': 177, 'dtmf_count': 4, 'dtmf_chars': ['1'\
, '2', '1', '#']}

 #  All Splice Commands and Descriptors have a load method


>>>> dscrptr.load(data)

>>>> dscrptr
{'tag': 1, 'descriptor_length': 10, 'identifier': 'CUEI', 'bites': None, 'name': 'DTMF Descriptor', 'preroll': 177, 'dtmf_count': 4, 'dtmf_chars': ['1', '2', '1', '#']}


  # Append to cue.descrptors


>>>> cue.descriptors.append(dscrptr)
  # Run encode to generate new Base64 string
>>>> cue.encode()
b'/DA7AAAAAAAA///wFAVIAACPf+/+c2nALv4AUsz1AAAAAAAWAAhDVUVJAAABNQEKQ1VFSbGfMTIxI55FecI='
```

  </detasils> 
 
</details>




