# nus_modem_full_version

The server-client pair of codes in this directory, which are modified version of those 
[in the parent directory](https://github.com/ekspla/micropython_aioble_examples), 
are capable of handling both of SOH (128) and STX (1024 byte) YMODEM blocks on Nordic UART service.  

`nus_modem_full_ver/nus_modem_server.py` uses STX blocks in YMODEM if MTU greater than 23 (default) is 
negotiated by MTU exchange, except for block number 0 (SOH) in which the size of the content (file name, size 
and zero paddings) is very limited.  

`nus_modem_full_ver/nus_modem_client.py` can handle both of the SOH and STX blocks by using the headers of the 
blocks sent from the server, thus it is also compatible to 
[the server code in the parent directory](https://github.com/ekspla/micropython_aioble_examples/blob/main/nus_modem_server.py) 
that uses exclusively SOH blocks.  

`nus_modem_full_ver/bleak_nus_modem_client.py` is a CPython/[bleak](https://github.com/hbldh/bleak) version of 
the client code compatible to both of the server codes as well.  It is tested on Linux and Windows 10/11. 
On Windows 11, it tries to change connection parameters to *ThroughputOptimized* (see below) via WinRT's 
*RequestPreferredConnectionParameters* method.  

The parameters stored in my Windows 11/Intel Wireless machine were read as followings  
``` shell
>>> import platform
>>> platform.system()
'Windows'
>>> platform.version()
'10.0.22631'
>>> import winrt.windows.devices.bluetooth as bt
>>> print(bt.BluetoothLEPreferredConnectionParameters.throughput_optimized.max_connection_interval)
12
>>> 12*1.25
15.0
>>> print(bt.BluetoothLEPreferredConnectionParameters.throughput_optimized.min_connection_interval)
12
>>> 12*1.25
15.0
>>>

 ...
```
and summerized (in milliseconds) in the table below.  Because Windows 11 OS always tries to change to 
*Balanced* (default) in idle, the other parameters should be specified just before the critical part.  

|  | MaxConnectionInterval | MinConnectionInterval | Measured Interval | Throughput / kbps |
| ------------------- | --- | --- | --- | --- | 
| ThroughputOptimized | 15.0 | 15.0 | 15.0 | 125.7 |
| Balanced | 60.0 | 30.0 | 60.0 | 55.5 |
| PowerOptimized | 180.0 | 90.0 | 180.0| 18.7 | 

