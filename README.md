# micropython_aioble_examples
A few aioble (asyncio bluetooth low energy) examples of Micropython using ESP32

(C) 2023-2024 [ekspla](https://github.com/ekspla/micropython_aioble_examples)

The following examples were tested with [micropython](https://micropython.org/) 1.21.0-1.23.0 and [aioble](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble) on [ESP32-DevKitC-32E](https://www.espressif.com/en/products/devkits/esp32-devkitc).


## Read measured values from a [HIOKI](https://www.hioki.com/) voltmeter via BLE
```hioki_z3210.py```

An example to read measured values from HIOKI's voltmeter, DT4261, via [Z3210 BLE interface](https://www.hioki.com/global/products/specialized-solutions/connecting-instruments/id_6780).
Other mesurement tools of HIOKI equipped with the BLE interface may also work (with/without a bit of modification).
Though the ways (e.g. commands; [references](https://www.hioki.com/global/support/download/software/versionup/detail/id_235) available from their website) to communicate with the tools are similar to those of USB ([DT4900-01](https://www.hioki.com/global/support/download/software/versionup/detail/id_235)), RS232 and GPIB interfaces, 
I found this BLE interface very useful in probing hazardous high voltages/currents at a safe place because of the wireless nature.  

I feel like using a home-built tiny display device equipped with an ESP32 is more convenient than using HIOKI's proprietary software with a smartphone.

```python
MicroPython v1.21.0 on 2023-10-05; Generic ESP32 module with ESP32
Type "help()" for more information.
>>>
>>> import hioki_z3210
>>> hioki_z3210.start()
Device(ADDR_PUBLIC, a4:9e:69:xx:yy:zz)
Connecting to Device(ADDR_PUBLIC, a4:9e:69:xx:yy:zz)
Connected.
(2023, 10, 26, 9, 37, 3, 3, 299)        +1.00000000E-04
(2023, 10, 26, 9, 37, 3, 3, 299)        +1.00000000E-04
(2023, 10, 26, 9, 37, 4, 3, 299)        +1.00000000E-04
(2023, 10, 26, 9, 37, 4, 3, 299)        +1.00000000E-04

 ...
 
```

## Read heart rate values from a heart rate sensor via BLE
```hr_read.py```

An example to read heart rate values (BPM) from [Magene's H64](https://support.magene.com/hc/en-us/categories/900000170623-H64-Heart-Rate-Sensor).  
Change the device name ```_HR_SENSOR_NAME``` or the ```address``` to specify your device.  The code should work for most of the BLE heart-rate 
sensors because the service and the characteristics are common.

```python
MicroPython v1.21.0 on 2023-10-05; Generic ESP32 module with ESP32
Type "help()" for more information.
>>>
>>> import hr_read
>>> hr_read.start()
Connecting to Device(ADDR_RANDOM, d8:75:ba:xx:yy:zz)
(2000, 1, 1, 6, 27, 59, 5, 1)	45
(2000, 1, 1, 6, 28, 0, 5, 1)	45
(2000, 1, 1, 6, 28, 1, 5, 1)	45
(2000, 1, 1, 6, 28, 2, 5, 1)	46

 ...

```

## Handling of connections to multiple peripherals and disconnect/reconnect
```conn_multiple.py```

Based on the codes of voltmeter and heart rate monitor, an example is shown.

You may want to change the maximum allowed number of connections in bluetooth stack.  
ESP32_GENERIC ([ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/kconfig.html)) for example, 
change ```CONFIG_BT_NIMBLE_MAX_CONNECTIONS``` and ```CONFIG_BTDM_CTRL_BLE_MAX_CONN``` in config file (default to 4 and 3, 
respectively). I have changed these (to 5 and 4) and got successfull concurrent connections to 4 peripherals.

If you have to find peripheral devices, write and use a loop of scan/connect/service-discovery to list the target devices in the beginning.
```
Connecting to Device(ADDR_RANDOM, d8:75:ba:xx:yy:zz)             # Heart rate sensor, switched on.
Connected. <DeviceConnection object at 3ffedf70>
Connecting to Device(ADDR_PUBLIC, a4:9e:69:xx:yy:zz)             # Voltmeter DT4261, switched off.
(2024, 5, 22, 7, 32, 27, 2, 143)        48 [bpm]
(2024, 5, 22, 7, 32, 29, 2, 143)        48 [bpm]
(2024, 5, 22, 7, 32, 30, 2, 143)        48 [bpm]
(2024, 5, 22, 7, 32, 31, 2, 143)        48 [bpm]
Timeout during connection
(2024, 5, 22, 7, 32, 32, 2, 143)        48 [bpm]
(2024, 5, 22, 7, 32, 34, 2, 143)        48 [bpm]
(2024, 5, 22, 7, 32, 35, 2, 143)        48 [bpm]
Connecting to Device(ADDR_PUBLIC, a4:9e:69:xx:yy:zz)             # Power on DT4261.
Connected. <DeviceConnection object at 3fff1240>
(2024, 5, 22, 7, 32, 37, 2, 143)        47 [bpm]
(2024, 5, 22, 7, 32, 37, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 37, 2, 143)        47 [bpm]
(2024, 5, 22, 7, 32, 38, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 38, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 39, 2, 143)        47 [bpm]
(2024, 5, 22, 7, 32, 39, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 40, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 40, 2, 143)        47 [bpm]
(2024, 5, 22, 7, 32, 40, 2, 143)        DT4261;-1.00000000E-04
(2024, 5, 22, 7, 32, 41, 2, 143)        DT4261;-1.00000000E-04
(2024, 5, 22, 7, 32, 41, 2, 143)        46 [bpm]
(2024, 5, 22, 7, 32, 42, 2, 143)        DT4261;-1.00000000E-04
(2024, 5, 22, 7, 32, 42, 2, 143)        DT4261;-1.00000000E-04
(2024, 5, 22, 7, 32, 43, 2, 143)        46 [bpm]
Error!                                                           # Power off DT4261.
(2024, 5, 22, 7, 32, 44, 2, 143)        45 [bpm]
(2024, 5, 22, 7, 32, 45, 2, 143)        45 [bpm]
(2024, 5, 22, 7, 32, 46, 2, 143)        46 [bpm]
Connecting to Device(ADDR_PUBLIC, a4:9e:69:xx:yy:zz)
(2024, 5, 22, 7, 32, 48, 2, 143)        46 [bpm]
(2024, 5, 22, 7, 32, 49, 2, 143)        45 [bpm]
(2024, 5, 22, 7, 32, 51, 2, 143)        46 [bpm]
(2024, 5, 22, 7, 32, 52, 2, 143)        45 [bpm]
Timeout during connection
(2024, 5, 22, 7, 32, 53, 2, 143)        45 [bpm]
(2024, 5, 22, 7, 32, 55, 2, 143)        45 [bpm]
(2024, 5, 22, 7, 32, 55, 2, 143)        45 [bpm]
(2024, 5, 22, 7, 32, 57, 2, 143)        45 [bpm]
Connecting to Device(ADDR_PUBLIC, a4:9e:69:xx:yy:zz)             # Power on DT4261 again.
Connected. <DeviceConnection object at 3ffd3450>
(2024, 5, 22, 7, 32, 58, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 58, 2, 143)        46 [bpm]
(2024, 5, 22, 7, 32, 59, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 32, 59, 2, 143)        DT4261;+0.00000000E+00
(2024, 5, 22, 7, 33, 0, 2, 143)         46 [bpm]
(2024, 5, 22, 7, 33, 0, 2, 143)         DT4261;+0.00000000E+00
(2024, 5, 22, 7, 33, 1, 2, 143)         DT4261;-1.00000000E-04
(2024, 5, 22, 7, 33, 1, 2, 143)         46 [bpm]
(2024, 5, 22, 7, 33, 1, 2, 143)         DT4261;-1.00000000E-04
(2024, 5, 22, 7, 33, 2, 2, 143)         DT4261;-1.00000000E-04
(2024, 5, 22, 7, 33, 2, 2, 143)         45 [bpm]
(2024, 5, 22, 7, 33, 3, 2, 143)         DT4261;-1.00000000E-04
(2024, 5, 22, 7, 33, 3, 2, 143)         45 [bpm]
(2024, 5, 22, 7, 33, 3, 2, 143)         DT4261;-1.00000000E-04
(2024, 5, 22, 7, 33, 4, 2, 143)         DT4261;-1.00000000E-04
main_hr closed                                                   # Stop the loop.
(2024, 5, 22, 7, 33, 4, 2, 143)         DT4261;-1.00000000E-04
main_4261 closed
End.

```

## How can we handle successive notified packets as a client using aioble?
(A link to discussion of this topic can be found 
[here](https://github.com/orgs/micropython/discussions/15544).)

In the current version of ```aioble/client.py```, a data of a notified 
packet can be overwritten by those of the successive notified packets in 
the queue to which the data are appended.  This is because the size of the 
queue by default is 1:  ```self._notify_queue = deque((), 1)```

So *a ```while True:``` loop* with *a ```charateristic.notified()```* 
shown in the official examples, as well as ```hr_read.py``` shown above, are not 
necessarily useful; **notified packets should be well separated in time**.

Though I do not know exactly what is the future plan of the developers to 
solve the issue, there is a comment in ```aioble/client.py``` as follows:
```
# Append the data. By default this is a deque with max-length==1, so it
# replaces. But if capture is enabled then it will append.
```

As a workaround for Nordic UART client used in [mpy_xoss_sync.py](https://github.com/ekspla/xoss_sync), 
I changed the size of the queue and retrieved the accumulated notified data from the queue as followings.
``` python
buffer = bytearray()
async with connection:
    service = await connection.service(_SERVICE_UUID) # A Nordic UART Service.
    tx_characteristic = await service.characteristic(_TX_CHARACTERISTIC_UUID)
    rx_characteristic = await service.characteristic(_RX_CHARACTERISTIC_UUID)
    tx_characteristic._notify_queue = deque((), 7) # Change the size of the queue.
    await self.tx_characteristic.subscribe(notify=True)

    while True:
         await request_transport(rx_characteristic) # Send command to request transport.
         data = await tx_characteristic.notified()
         await asyncio.sleep(1) # Wait until the queue is filled.
         buffer.extend(data)
         while len(queue := tx_characteristic._notify_queue) >= 1:
             buffer.extend(queue.popleft())
         tx_characteristic._notify_event.clear() # Make sure to clear the flag.

         # Do something with the buffer.
```

The workaround is useful in this case because the server (peripheral) always waits for the response of the 
chunk of data from the client (micropython/aioble) before going to the next, and this waiting time can be used 
by the client to process (e.g. concatinate) the data in the queue.


A pair of test codes, ```nus_modem_client.py``` and ```nus_modem_server.py```, were prepared as the complete 
set of working example.  In this case, a primitive YMODEM file transfer protocol was implemented on 
[Nordic UART service's](https://docs.nordicsemi.com/bundle/ncs-latest/page/nrf/libraries/bluetooth_services/services/nus.html) 
TX/RX channels.  Athough there are limitations as described below, it works well as expected and has been 
already applied to [one of my projects](https://github.com/ekspla/xoss_sync).

The throughput measured was 27.7 kbps using 7.5 ms connection interval and tick rate of 1 ms (CONFIG_FREERTOS_HZ=1000) 
with ESP32-S3-WROOM-1-N16R8 and micro-SD card, while the theoretical limit assuming 3 connection events/128-byte data block 
is 45.5 kbps.

The limitations are due mainly to the implementation of YMODEM in part as follows:
- The script expects a transport with MTU of 23, 128-byte data per block, and CRC16/ARC (not CRC16/XMODEM).
Larger MTU by DLE (Data Length Extension) and 1024-byte data in YMODEM (STX), that make throughput higher, are not 
supported (not implemented yet).
