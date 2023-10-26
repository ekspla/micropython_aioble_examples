import sys

sys.path.append("")

from micropython import const

import asyncio
import aioble
import bluetooth

import time

#address = "a4:9e:69:xx:yy:zz"
address = None
_Z3210_GENERICACCESS_UUID = bluetooth.UUID(0x1800)
_Z3210_GENERICATTRIBUTE_UUID = bluetooth.UUID(0x1801)
_Z3210_DEVICEINFORMATION_UUID = bluetooth.UUID(0x180a)
_Z3210_BATTERY_UUID = bluetooth.UUID(0x180f)

_Z3210_SCANPARAMETERS_UUID = bluetooth.UUID(0x1813)
_Z3210_SCANINTERVALWINDOW_UUID = bluetooth.UUID(0x2a4f)
_Z3210_SCANREFRESH_UUID = bluetooth.UUID(0x2a31)

_Z3210_HID_UUID = bluetooth.UUID(0x1812) # HID
_Z3210_HIDINFORMATION_UUID = bluetooth.UUID(0x2a4a)
_Z3210_REPORTMAP_UUID = bluetooth.UUID(0x2a4b)
_Z3210_HIDCONTROLPOINT_UUID = bluetooth.UUID(0x2a4c)
_Z3210_REPORT_UUID = bluetooth.UUID(0x2a4d)
_Z3210_PROTOCOLMODE_UUID = bluetooth.UUID(0x2a4e)

_Z3210_UNKNOWN1_UUID = bluetooth.UUID('1d14d6ee-fd63-4fa1-bfa4-8f47b42119f0')
_Z3210_UNKNOWN1_CHAR_UUID = bluetooth.UUID('f7bf3564-fb6d-4e53-88a4-5e37e0326063')

_Z3210_UNKNOWN2_UUID = bluetooth.UUID('275ce3d8-b906-4475-8dd7-76af0db742bf')
_Z3210_UNKNOWN2_CHAR1_UUID = bluetooth.UUID('78b028ce-affd-4967-ab9e-dc336c8c94e7') # This is used for communication.
_Z3210_UNKNOWN2_CHAR2_UUID = bluetooth.UUID('872f065a-5297-4483-9183-27cd72f7cffc')

async def find_voltmeter():
    # Scan for 5 seconds, in active mode, with very low interval/window (to
    # maximise detection rate).
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            # See if it matches the name and the service.
            #print(result.name())
            #e.g. "Z3210V2.10:DT4261#xxxxxxxxx", where DT4261 and xxxxxxxxx are model number and the serial number.
            if str(result.name())[:10] == "Z3210V2.10" and _Z3210_HID_UUID in result.services():
                print(result.device)
                return result.device
    return None

async def main():
    if address:
        device = aioble.Device(aioble.ADDR_PUBLIC, address)
    else:
        device = await find_voltmeter()
    if not device:
        print("Voltmeter not found")
        return

    try:
        print("Connecting to", device)
        connection = await device.connect(timeout_ms=5000)
    except asyncio.TimeoutError:
        print("Timeout during connection")
        return

    async with connection:
        try:
            z3210_service = await connection.service(_Z3210_UNKNOWN2_UUID)
            z3210_characteristic = await z3210_service.characteristic(_Z3210_UNKNOWN2_CHAR1_UUID)
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            return

        print("Connected.")
        await z3210_characteristic.subscribe(indicate=True)
        while True:
            try:
                #print(z3210_service)
                #print(z3210_characteristic)

                # Line termination (\r\n) is necessary in each command.
                # The way to communicate is similar to those of USB (DT4900-01), RS232C and GPIB interfaces of HIOKI.
                #await z3210_characteristic.write(bytes(':FETCCNT?\r\n', 'utf-8')) # Request for int number of counts.
                await z3210_characteristic.write(bytes('FETC?\r\n', 'utf-8')) # Request for floating point numbers.

                z3210_data = await z3210_characteristic.indicated(timeout_ms=1000)
                if z3210_data: print(f"{time.localtime()}\t{z3210_data.decode()}")
                #_z3210_data_handler(z3210_data)

                await asyncio.sleep_ms(100)

            except Exception as e:
                print(e)
                print(type(e))
                print("DeviceDisconnected Exit")
                #pass
                return

def start():
    asyncio.run(main())
