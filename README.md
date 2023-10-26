# micropython_aioble_examples
A few aioble (asyncio BLE) examples of micropython using esp32

(C) 2023 [ekspla](https://github.com/ekspla/micropython_aioble_examples)

The following examples were tested with micropython 1.21.0 with aioble on ESP32-DevKitC-32E.


## Read measured voltages from [HIOKI](https://www.hioki.com/) voltmeter via BLE

An example to read measured values from HIOKI's voltmeter, DT4261, via [Z3210 BLE interface](https://www.hioki.com/global/products/specialized-solutions/connecting-instruments/id_6780).
Other mesurement tools of HIOKI equipped with the BLE interface may work (with/without a bit of modification).
The ways (e.g. commands; references available from their website) to communicate with the tools are similar to those of USB, RS232 and GPIB interfaces.

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

An example to read heart rate from Magene's H64.  Change the device name or the address to specify your device.

```python

```

