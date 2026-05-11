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

After a bit of modification, the code successfully worked on Linux/Bleak also with 
[Bumble backend](https://github.com/ekspla/bleak-bumble_dev_host_mode) / [Google Bumble](https://github.com/google/bumble) 
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

### Linux (and also Windows) with Bumble Backend  

In contrast to BlueZ backend, the parameters were easily changed as followings with the Bumble backend.  

Thanks to the cross-platform [Google-Bumble's](https://github.com/google/bumble) Bluetooth host stack implemented in 
CPython, the exact same code was confirmed to work on Windows 7 sp1 using [VxKex](https://github.com/i486/VxKex).  

``` Python
backend = client._backend
mtu_size = await backend._peer.request_mtu(209)
#mtu_size = await backend._peer.request_mtu(512)
await asyncio.sleep(4)

await self.start_notify(client, TX_CHARACTERISTIC_UUID)

await backend._connection.update_parameters(
    # Valid for bumble==0.0.211; the format has been changed to ms in the later versions.
    connection_interval_min = 6, # 7.5 ms
    connection_interval_max = 6,
    #connection_interval_min = 12, # 15.0 ms
    #connection_interval_max = 12,
    #connection_interval_min = 48, # 60.0 ms
    #connection_interval_max = 48,
    #connection_interval_min = 144, # 180.0 ms
    #connection_interval_max = 144,
    max_latency = 0, # 0
    supervision_timeout = 200, # 200 * 10 = 2000 ms
)
await asyncio.sleep(1)
```

Measured Throughputs / kbps  

| connection interval | 7.5 | 15.0 | 60.0 | 180.0 |
| ------------------- | --- | --- | --- | --- |
| mtu=23 | 28.6 | 20.7 | 8.5 | 2.8 |
| mtu=209 | 117.9 | 110.9 | 85.7 | 22.4 |
| mtu=512 (same as Win11) | 104.8 | 104.8 | 49.6 | 22.4 |

The code also successfully worked by using TP-Link UB500 (BT v5.4, RTL8761 chip) with 
`rtl8761b_fw.bin/rtl8761b_config.bin` (not the default RTL8761BU firmwares); 
it shows a bit less performance though.  

| connection interval | 7.5 | 15.0 | 60.0 | 180.0 |
| ------------------- | --- | --- | --- | --- |
| mtu=209 | 78.5 | 70.1 | 24.2 | 7.8 |

Update:  
With the latest (Nov 2025) firmware extracted from Windows driver of TP-Link, 
throughputs were similar to those of UB400 (CSR8510 chip).

### Virtual Server and Client on Bumble's `LocalLink()`  

Thinking the other way around, we can make use of Bumble's virtual HCI H4 controllers for both 
the server and the client.  These *virtual controllers* may be useful in tests and developments. 
We can also use a sniffer built in Bumble. *Absolutely no hardware*.  

- Instead of PTYs, I used a kernel module of [tty0tty](https://github.com/freemed/tty0tty) to 
emulate serial ports with hardware flow control. In this case, /dev/tnt0 -- /dev/tnt1, ..., 
/dev/tnt6 -- /dev/tnt7 were tied together. On Windows, use [com0com](https://com0com.sourceforge.net/).  
```shell
ls -la /dev/tnt*
crw-rw----. 1 root dialout 241, 0 May 10 13:29 /dev/tnt0
crw-rw----. 1 root dialout 241, 1 May 10 13:29 /dev/tnt1
crw-rw----. 1 root dialout 241, 2 May 10 13:29 /dev/tnt2
crw-rw----. 1 root dialout 241, 3 May 10 13:29 /dev/tnt3
crw-rw----. 1 root dialout 241, 4 May 10 12:49 /dev/tnt4
crw-rw----. 1 root dialout 241, 5 May 10 12:49 /dev/tnt5
crw-rw----. 1 root dialout 241, 6 May 10 12:49 /dev/tnt6
crw-rw----. 1 root dialout 241, 7 May 10 12:49 /dev/tnt7
```
- Run two virtual HCI controllers for `/dev/tnt1` and `/dev/tnt3` on a Bumble's `LocalLink()`.  
```shell
python lib/python3.12/site-packages/bumble/apps/controllers.py \
serial:/dev/tnt1,1000000,rtscts \
serial:/dev/tnt3,1000000,rtscts
```

- Open the second console and run the server.  
``` python
pyenv shell micropython-1.23.0
MICROPYBTUART=/dev/tnt0 python
MicroPython v1.23.0 on 2024-11-18; linux [GCC 11.5.0] version
Use Ctrl-D to exit, Ctrl-E for paste mode
>>> from bluetooth import BLE
>>> BLE().active(1)
True
>>>
>>> import nus_modem_server
>>> nus_modem_server.start()
```

- Finally, open the third console and run the client on CPython/Bleak-Bumble. 
This client can be another MPY-Linux with the aioble version of client.  
``` python
BLEAK_BUMBLE = "serial:/dev/tnt2,1000000,rtscts"
BLEAK_BUMBLE_HOST = "1"
python bleak_nus_modem_client.py
Scanning for Bluetooth devices...
 BLEDevice(E3:C3:5C:4A:77:A4, mpy-nus) with AdvertisementData(local_name='mpy-nus', service_uuids=['6e400001-b5a3-f393-e0a9-e50e24dcca9e'], tx_power=127, rssi=-50)
Found target device: E3:C3:5C:4A:77:A4: mpy-nus
Connected to E3:C3:5C:4A:77:A4: mpy-nus
Device Name: mpy-nus
Client Name: mpy-nus
MTU 23
mtu: 209
Notifications started
Mon May 10 13:29:17 2026
Successfully wrote combined data to test.bin  # 235,723 bytes * 8 bit/byte / 13 sec = 145.1 kbps
Mon May 10 13:29:30 2026
```
