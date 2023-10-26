# micropython_aioble_examples
A few aioble (asyncio BLE) examples of [micropython](https://micropython.org/) using esp32

(C) 2023 [ekspla](https://github.com/ekspla/micropython_aioble_examples)

The following examples were tested with micropython 1.21.0 with [aioble](https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble) on [ESP32-DevKitC-32E](https://www.espressif.com/en/products/devkits/esp32-devkitc).


## Read measured voltages from [HIOKI](https://www.hioki.com/) voltmeter via BLE

An example to read measured values from HIOKI's voltmeter, DT4261, via [Z3210 BLE interface](https://www.hioki.com/global/products/specialized-solutions/connecting-instruments/id_6780).
Other mesurement tools of HIOKI equipped with the BLE interface may also work (with/without a bit of modification).
The ways (e.g. commands; [references](https://www.hioki.com/global/support/download/software/versionup/detail/id_235) available from their website) to communicate with the tools are similar to those of USB ([DT4900-01](https://www.hioki.com/global/support/download/software/versionup/detail/id_235)), RS232 and GPIB interfaces.

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

## Read heart rate from a herat rate belt via BLE

An example to read heart rate values (BPM) from [Magene's H64](https://support.magene.com/hc/en-us/categories/900000170623-H64-Heart-Rate-Sensor).  Change the device name ```_HR_SENSOR_NAME``` or the ```address``` to specify your device.

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

