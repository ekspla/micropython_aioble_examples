# micropython_aioble_examples
A few aioble (asyncio bluetooth low energy) examples of MicroPython using ESP32

(C) 2023-2025 [ekspla](https://github.com/ekspla/micropython_aioble_examples)

The following examples were tested with [MicroPython](https://micropython.org/) 1.21.0-1.23.0 and 
[aioble](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble) on 
[ESP32-DevKitC-32E](https://www.espressif.com/en/products/devkits/esp32-devkitc).


## Read measured values from a [HIOKI](https://www.hioki.com/) voltmeter via BLE
`hioki_z3210.py`

An example to read measured values from HIOKI's voltmeter, DT4261, via 
[Z3210 BLE interface](https://www.hioki.com/global/products/specialized-solutions/connecting-instruments/id_6780).
Other mesurement tools of HIOKI equipped with the BLE interface may also work (with/without a bit of modification).
Though the ways (e.g. commands; [references](https://www.hioki.com/global/support/download/software/versionup/detail/id_235) 
available from their website) to communicate with the tools are similar to those of 
USB ([DT4900-01](https://www.hioki.com/global/support/download/software/versionup/detail/id_235)), RS232 and GPIB interfaces, 
I found this BLE interface very useful in probing hazardous high voltages/currents at a safe place because of the wireless nature.  

I feel like using a home-built tiny display device equipped with an ESP32 is more convenient than using HIOKI's proprietary 
software with a smartphone.

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
`hr_read.py`

An example to read heart rate values (BPM) from 
[Magene's H64](https://support.magene.com/hc/en-us/categories/900000170623-H64-Heart-Rate-Sensor).  
Change the device name `_HR_SENSOR_NAME` or the `address` to specify your device.  The code should work for most 
of the BLE heart-rate sensors because the service and the characteristics are common.

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
`conn_multiple.py`

Based on the codes of voltmeter and heart rate monitor, an example is shown.

You may want to change the maximum allowed number of connections in bluetooth stack.  
ESP32_GENERIC ([ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/kconfig.html)) for example, 
change `CONFIG_BT_NIMBLE_MAX_CONNECTIONS` and `CONFIG_BTDM_CTRL_BLE_MAX_CONN` in config file (default to 4 and 3, 
respectively). I have changed these (to 5 and 4) and got successfull concurrent connections to 4 peripherals.

If you have to find peripheral devices, write and use a loop of scan/connect/service-discovery to list the target devices 
in the beginning.

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

In the current version of `aioble/client.py`, a data of a notified 
packet can be overwritten by those of the successive notified packets in 
the queue to which the data are appended.  This is because the size of the 
queue by default is 1:  `self._notify_queue = deque((), 1)`

So *a `while True:` loop* with *a `charateristic.notified()`* 
shown in the official examples, as well as `hr_read.py` shown above, are not 
necessarily useful; **notified packets should be well separated in time from each other**.

Though I do not know exactly what is the future plan of the core developers to 
solve the issue, there is a comment in `aioble/client.py` as follows:

```
# Append the data. By default this is a deque with max-length==1, so it
# replaces. But if capture is enabled then it will append.
```

As a workaround for Nordic UART client used in [mpy_xoss_sync.py](https://github.com/ekspla/xoss_sync), 
I changed the size of the queue and retrieved the accumulated notified data from the queue as followings.

```python
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


A pair of test codes, `nus_modem_client.py` and `nus_modem_server.py`, were prepared as the complete 
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

Update MAR 2025: 
[A full-featured version of the pair was also prepared](https://github.com/ekspla/micropython_aioble_examples/blob/main/nus_modem_full_ver/) 
to test the higher throughput.  Using conn_intervals = 7.5 ms, STX (1024-byte block) and fragmentation of MTU = 209 via L2CAP 
94.3 kbps was obtained.  Further increase in throughput would require `LE Data Length Extension` and `LE 2M PHY`.


## ESP32 chip as a USB bluetooth dongle (HCI H4) for use with unix-port (Linux) of micropython and aioble

A cheap USB bluetooth dongle was easily built by using an ESP32, a USB-UART chip ([CH340E](https://www.wch.cn/search?t=all&q=CH340E)) 
and a 600-mA LDO ([RT9080](https://www.richtek.com/Products/Linear%20Regulator/Single%20Output%20Linear%20Regulator/RT9080?sc_lang=en)). 
As shown in the figures below, I tried to reduce the lengths of the cables as short as possible to obtain the 
highest reliable speed.  USB-UART/LDO built on frontside and ESP32 mounted on backside were sticked together to form the 
home-made USB dongle. 
![PHOTO_FRONTSIDE_CH340_LDO](https://github.com/ekspla/micropython_aioble_examples/blob/main/figs/Frontside_CH340_LDO.jpg "Frontside")
![PHOTO_BACKSIDE_ESP32](https://github.com/ekspla/micropython_aioble_examples/blob/main/figs/Backside_ESP32.jpg "Backside")

The firmware on the ESP32, which was written through the pin sockets shown in the photo above, was built on `controller_hci_uart_esp32`, 
[an example of Espressif's ESP-IDF](https://github.com/espressif/esp-idf/tree/master/examples/bluetooth/hci), with the following parameters.

UART baudrate = 1 Mbps; 
hardware flow control; 
FreeRTOS tick rate = 1 ms; 
CPU frequency = 240 MHz; 
GPIO pins 5, 18, 23, 19 are used as TxD, RxD, CTS, RTS, respectively.

I had to modify the codes as followings to set the parameters as above.

Modify `ESP-IDF/components/bt/controller/esp32/Kconfig.in`:

``` Diff
    config BTDM_CTRL_HCI_UART_BAUDRATE
        int "UART Baudrate for HCI"
        depends on BTDM_CTRL_HCI_MODE_UART_H4
-       range 115200 921600
-       default 921600
+       range 115200 3000000
+       default 1000000
        help
```
Modify `sdkconfig.defaults`:

```
CONFIG_BT_BLUEDROID_ENABLED=n
CONFIG_BT_CONTROLLER_ONLY=y
CONFIG_BTDM_CTRL_HCI_MODE_UART_H4=y
CONFIG_BTDM_CTRL_HCI_UART_NO=1
CONFIG_BTDM_CTRL_HCI_UART_BAUDRATE=1000000
CONFIG_BTDM_CTRL_MODEM_SLEEP=n

# Other config
CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240=y
CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ=240
CONFIG_FREERTOS_HZ=1000
```
Run `idf.py menuconfig`, then `idf.py build`.

To use the other baudrate, you have to modify it also in `MPY/ports/unix/mpbthciport.c`, which defaults to 1 Mbps. 
Because I could not obtain reliable connections at 1.5, 2 and 3 M bps, the baudrate was set to 1 Mbps in my case.

[The MPY on Linux machine using NimBLE stack was built](https://github.com/orgs/micropython/discussions/10234) as 
follows: 

``` Shell
make -C ports/unix MICROPY_PY_BLUETOOTH=1 MICROPY_BLUETOOTH_NIMBLE=1
```

Because the built-in USB-UART kernel module did not work reliably at a very high speed, I had to compile the module 
using the latest source code (V1.8 on 2024.08) of the manufacturer (WCH) obtained from 
[their website](http://www.wch.cn/download/CH341SER_LINUX_ZIP.html) 
or from [their github repository](https://github.com/WCHSoftGroup/ch341ser_linux). Default latency of the UART using 
this module was minimized by an `ASYNC_LOW_LATENCY` flag in the source code. 
Before start using it, set an appropriate permission of the USB-UART device you are using (e.g. `chmod 666` or `adduser` 
to the `dialout` group).

You have to specify the USB-UART device if it is not `/dev/ttyUSB0` as written in `MPY/ports/unix/mpbthciport.c`.

In my case `MICROPYBTUART=/dev/ttyCH341USB0`:

``` Python
MICROPYBTUART=/dev/ttyCH341USB0 micropython
MicroPython v1.23.0 on 2024-11-18; linux [GCC 11.5.0] version
Use Ctrl-D to exit, Ctrl-E for paste mode
>>> from bluetooth import BLE
>>> BLE().active(1)
True
>>> import aioble
>>> 
```

This dongle/unix-port MPY combination was successfully used with my aioble test code, 
[nus_modem_client.py](https://github.com/ekspla/micropython_aioble_examples/blob/main/nus_modem_client.py), 
in this repository.

Additional notes:  
 - You can also use this USB dongle from the other softwares such as [BlueZ](https://github.com/bluez/bluez), 
[BTstack](https://github.com/bluekitchen/btstack) and 
[Google Bumble](https://github.com/google/bumble) because the APIs of HCI H4 are common.  

 - It may be wise for Windows users to stick on to the old WCH's driver version (V3.5 on 2019), while the latest one works great on Linux as shown above. 
[As reported in this forum](https://answers.microsoft.com/en-us/windows/forum/all/usb-serial-ch340-chipset-not-working-after-windows/88b0ab19-9e1b-46bb-82d4-f806e34b2ed9),
a few percent of my devices stops working with updated V3.9 driver on Windows.  I am not quite sure if the non-working chips are of counterfeit though.

 - A note for users of MicroPython on Windows port:  

There is [a long standing PR from a core developer](https://github.com/micropython/micropython/pull/7781) 
to implement NimBLE on Windows port of MicroPython.  

One of the most big issue to use this PR *in my case* was latencies in USB serial devices. 
The default latency of 16 ms/packet and a large USB buffer size made serial communications (HCI H4) 
unreliable. In worst-case scenario with a 4096-byte USB buffer (64 packet * 64 bytes/packet), 
this latency resuts in 64 packet * 16 ms = 1024 ms delay, which is not tolerable.  

The best workaround would be to use a legacy COM port (such as 16550A), which is not available 
in most of the PCs these days. Another workaround is to decrease the USB latency timer and/or the 
buffer size of the device from properties in the device manager, which is not available for all 
of the devices. FTDI drivers, for example, have these settings though. Changing the buffer size 
by SetupComm() almost always does not work for the USB serial devices.  

So an easy and versatile workaround for me was to force the device to flush the buffer when desired, 
but FlushFileBuffers() did not work for the USB. An application note 
[\(AN232B-04, FTDI\)](https://www.ftdichip.com/Documents/AppNotes/AN232B-04_DataLatencyFlow.pdf) 
describes that an unused modem status line (DSR in this case) can be used for this purpose; the 
buffer is flushed when the state of DTR tied to DSR is changed. This seems to work almost all 
of the USB serial devices that I have. In prior to ReadFile(), check if there is a character to 
be read in the queue with ClearCommError() and COMSTAT.cbInQueue. If not, change the state of DTR, 
wait some time (say, 1 ms) and check the queue once again. Avoid using Sleep(1) here because of 
system timer precision of ca. 16 ms.  

However, changing the state of DTR (and also RTS) by an API of EscapeCommFunction() does not 
necessarily work.  Note that the `usbser.sys` of Microsoft which is used by most of the USB CDC 
devices of today does not work, while some proprietary drivers such as FTDI's ones do.  

So a workaround here is using a sequence of GetCommState(), SetCommState() and EscapeCommFunction() 
to change the DTR state which is shown in [newlib-cygwin](https://sourceware.org/pipermail/cygwin-cvs/2022q4/015643.html) 
and also in 
[a Microsoft's code](https://github.com/microsoft/referencesource/blob/main/System/sys/system/IO/ports/SerialStream.cs).  

There is also a good instruction for how to set COMMTIMEOUTS with USB serial devices as a comment in 
the Microsoft's code shown above; ReadIntervalTimeout, ReadTotalTimeoutMultiplier and 
WriteTotalTimeoutMultiplier do not make sense in USB serial devices where characters are transferred 
in a packet.  
