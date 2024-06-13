# micropython_aioble_examples
A few aioble (asyncio bluetooth low energy) examples of Micropython using ESP32

(C) 2023-2024 [ekspla](https://github.com/ekspla/micropython_aioble_examples)

The following examples were tested with [micropython](https://micropython.org/) 1.21.0-1.23.0 and [aioble](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble) on [ESP32-DevKitC-32E](https://www.espressif.com/en/products/devkits/esp32-devkitc).


## Read measured values from a [HIOKI](https://www.hioki.com/) voltmeter via BLE
```hioki_z3210.py````

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
```hr_read.py````

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
```conn_multiple.py````

Based on the codes of voltmeter and heart rate monitor, an example is shown.

You may want to change the maximum allowed number of connections in bluetooth stack.  
ESP32 ([ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/kconfig.html)) for example, 
change either ```BT/BLE MAX ACL CONNECTIONS``` in menu or ```CONFIG_BT_ACL_CONNECTIONS``` in config file (defaults to 4, 
including scan and advertise).

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

