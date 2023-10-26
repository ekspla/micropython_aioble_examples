import sys

sys.path.append("")

from micropython import const

import asyncio
import aioble
import bluetooth

import random
import struct
import binascii
import time

address = "d8:75:ba:xx:yy:zz"
#address = None
_HR_SENSOR_NAME = "44278-33" # This is the name of my Magene's H64.

_HEART_RATE_SERVICE_UUID = bluetooth.UUID(0x180d)
_HEART_RATE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2a37)
#HEART_RATE_CHARACTERISTIC_UUID = "00002a37-0000-1000-8000-00805f9b34fb" # HR measurement 0x2a37
#BODY_SENSOR_LOCATION_UUID = "00002a38-0000-1000-8000-00805f9b34fb" # Body sensor location 0x2a38
#HEART_RATE_CONTROL_POINT_UUID = "00002a39-0000-1000-8000-00805f9b34fb" # HR control point 0x2a39


# Helper to decode the heart rate characteristic encoding.
def _heart_rate_data_handler(data):
    c_data = str(binascii.hexlify(data))
    #print(c_data)
    hr = int(c_data[4:6], 16) # Extract the second byte (0x31, 0x37) from c_data, such as "b'163187048704'" and "b'0637'".
    print(time.localtime(), '\t', hr, sep = '')

async def find_hr_sensor():
    # Scan for 5 seconds, in active mode, with very low interval/window (to
    # maximise detection rate).
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            # See if it matches the name and the service of the heart rate seonsor.
            if result.name() == _HR_SENSOR_NAME and _HEART_RATE_SERVICE_UUID in result.services():
                return result.device
    return None

_init = True
async def main():
    global _init

    if address:
        device = aioble.Device(aioble.ADDR_RANDOM, address)
    else:
        device = await find_hr_sensor()
    if not device:
        print("Heart rate sensor not found")
        return

    try:
        if _init:
            print("Connecting to", device)
        connection = await device.connect(timeout_ms=5000)
    except asyncio.TimeoutError:
        if _init:
            print("Timeout during connection")
        return
    _init = False

    async with connection:
        try:
            hr_service = await connection.service(_HEART_RATE_SERVICE_UUID)
            hr_characteristic = await hr_service.characteristic(_HEART_RATE_CHARACTERISTIC_UUID)
        except asyncio.TimeoutError:
            print("Timeout discovering services/characteristics")
            return

        await hr_characteristic.subscribe(notify=True)
        while True:
            try:
                heart_rate_data = await hr_characteristic.notified()
                _heart_rate_data_handler(heart_rate_data)
                await asyncio.sleep_ms(1000)
            except:
                #print("DeviceDisconnected Exit")
                return

def start():
    while True:
        asyncio.run(main())
