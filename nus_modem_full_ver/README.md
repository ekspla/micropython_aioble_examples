# nus_modem_full_featured_version

The server-client pair of codes in this directory, which are modified version of those 
[in the parent directory](https://github.com/ekspla/micropython_aioble_examples), 
are capable of handling both of SOH (128) and STX (1024 byte) YMODEM blocks on Nordic UART service.  

`nus_modem_full_ver/nus_modem_server.py` uses STX blocks in YMODEM if MTU greater than 23 (default) is 
negotiated by MTU exchange, except for block number 0 (SOH) in which the size of the content (consisting of 
file name, size and zero paddings) is very limited.  

`nus_modem_full_ver/nus_modem_client.py` can handle both of the SOH and STX blocks by using the headers of the 
blocks sent from the server, thus it is also compatible to 
[the server code in the parent directory](https://github.com/ekspla/micropython_aioble_examples/blob/main/nus_modem_server.py) 
that uses exclusively SOH blocks.  

`nus_modem_full_ver/bleak_nus_modem_client.py` is a CPython/[Bleak](https://github.com/hbldh/bleak) version of 
the client code compatible to both of the server codes as well.  It was tested on Linux (BlueZ backend) and 
Windows 10/11 (WinRT backend). 
On Windows 11, it tries to change connection parameters to *ThroughputOptimized* (see below) via WinRT's 
*RequestPreferredConnectionParameters* method.  
After a bit of modifications, the codes successfully worked on Linux/Bleak also with 
[Bumble backend](https://github.com/vChavezB/bleak-bumble) / [Google Bumble](https://github.com/google/bumble) 
and TP-Link BT dongle \(UB400, v4.0, CSR8510 chip\) by using HCI over USB (HCI H2). See below for details. 


## Note

### ESP32-S3 (240 MHz, `CONFIG_FREERTOS_HZ=1000`) / MicroPython  

Measured Throughputs / kbps

| connection interval | 7.5 |
| ------------------- | --- |
| mtu=23 | 27.7 |
| mtu=209 | 94.3 |

### Windows/WinRT Backend (mtu=512)
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

|  | Max Connection Interval | Min Connection Interval | Connection Latency | Link Timeout | Measured Interval | Throughput / kbps |
| ------------------- | --- | --- | --- | --- | --- | --- |
| ThroughputOptimized | 15.0 | 15.0 | 0 | 2000.0 | 15.0 | 125.7 |
| Balanced | 60.0 | 30.0 | 0 | 4000.0 | 60.0 | 55.5 |
| PowerOptimized | 180.0 | 90.0 | 0 | 6000.0 | 180.0 | 18.7 |

Bluetooth stacks on Windows OSs (10 and 11) always start connection with parameters of 60.0 ms interval, 0 latency and 9600 ms timeout.
They seem to ignore `Peripheral Preferred Connection Parameters` in peripheral's `Generic Access` and change the connection parameters very 
frequently when connected. `Peripheral Connection Interval Range` in advertising payload, if exists, is also ignored.  

The only way to control the parameters from Windows central is *`RequestPreferredConnectionParameters`* as described above. A negotiation 
using `Connection Parameters Request Procedure` would start on BT4.1 and above, while `LL_CONNECTION_UPDATE_IND` would be sent without the 
negotiation on BT4.0.  

The good things is that Administrator rights are not required on Windows/WinRT to change the parameters, while root or CAP_NET_ADMIN is 
required on Linux/bluetoothd. 

### Linux/Bumble Backend  

In contrast to BlueZ backend, the parameters were easily changed as followings with the Bumble backend.
``` Python
backend = client._backend
mtu_size = await backend._peer.request_mtu(209)
#mtu_size = await backend._peer.request_mtu(512)
await asyncio.sleep(4)

await self.start_notify(client, TX_CHARACTERISTIC_UUID)

await backend._connection.update_parameters(
    connection_interval_min = 6, # 7.5 ms
    connection_interval_max = 6, # 7.5 ms
    #connection_interval_min = 12, # 15.0 ms
    #connection_interval_max = 12, # 15.0 ms
    #connection_interval_min = 48, # 60.0 ms
    #connection_interval_max = 48, # 60.0 ms
    #connection_interval_min = 144, # 180.0 ms
    #connection_interval_max = 144, # 180.0 ms
    max_latency = 0, # 0
    supervision_timeout = 200, # 200 * 10 = 2000 ms
)
await asyncio.sleep(1)
```

Measured Throughputs / kbps  

| connection interval | 7.5 | 15.0 | 60.0 | 180.0 |
| ------------------- | --- | --- | --- | --- |
| mtu=23 | 28.6 |  |  |  |
| mtu=209 | 117.9 | 110.9 | 85.7 | 22.4 |
| mtu=512 (same as Win11) | 104.8 | 104.8 | 49.6 | 22.4 |
