import sys

sys.path.append('')

import asyncio
import aioble
import bluetooth
import machine
import time

# Constants and global variables
address_hr = 'd8:75:ba:xx:yy:zz'
address_dt4261 = 'a4:9e:69:xx:yy:zz'

_HEART_RATE_SERVICE_UUID = bluetooth.UUID(0x180d)
_HEART_RATE_CHARACTERISTIC_UUID = bluetooth.UUID(0x2a37)

_Z3210_UNKNOWN2_UUID = bluetooth.UUID('275ce3d8-b906-4475-8dd7-76af0db742bf')
_Z3210_UNKNOWN2_CHAR1_UUID = bluetooth.UUID('78b028ce-affd-4967-ab9e-dc336c8c94e7') # This is used for communication.

hr_task = dt4261_task = None
hr_active = dt4261_active = False # Connection state
stop = False # Loop stop flag

switch = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
def sw():
    return (not switch.value())

async def main_hr(conn, char):
    global hr_active

    try:
        while True:
            await asyncio.sleep(0)
            data = await char.notified()
            print(f'{time.localtime()}\t{data[1]} [bpm]')
            await asyncio.sleep_ms(500)
    except asyncio.CancelledError:
        print('main_hr closed')
        await conn.disconnect()
        return
    except aioble.DeviceDisconnectedError:
        print('DeviceDisconnectedError')
        hr_active = False
    except Exception as ex:
        print('Error!', ex)
        hr_active = False

    await conn.disconnected()
    return

async def main_4261(conn, char):
    global dt4261_active

    try:
        while True:
            await asyncio.sleep(0)
            await char.write(bytes('QPID;FETC?\r\n', 'utf-8')) # 
            data = await char.indicated(timeout_ms=1000)
            print(f'{time.localtime()}\t{data.decode()}')
            await asyncio.sleep_ms(500)
    except asyncio.CancelledError:
        print('main_4261 closed')
        await conn.disconnect()
        return
    except aioble.DeviceDisconnectedError:
        print('DeviceDisconnectedError')
        dt4261_active = False
    except Exception as ex:
        print('Error!', ex)
        dt4261_active = False

    await conn.disconnected()
    return

async def conn_multiple():
    global hr_task, dt4261_task, hr_active, dt4261_active

    while not stop:

        if not hr_active:
            await asyncio.sleep(0)

            device = aioble.Device(aioble.ADDR_RANDOM, address_hr)
            connection = None
            try:
                print('Connecting to', device)
                connection = await device.connect(timeout_ms=5000)
                if connection.is_connected():
                    print('Connected.', connection)

                    service = await connection.service(_HEART_RATE_SERVICE_UUID)
                    characteristic = await service.characteristic(_HEART_RATE_CHARACTERISTIC_UUID)
                    await characteristic.subscribe(notify=True)

                    hr_task = asyncio.create_task(main_hr(connection, characteristic))
                    hr_active = True
            except asyncio.TimeoutError:
                print("Timeout during connection")
                if connection is not None: await connection.disconnect()
            except Exception as ex: # Not sure if this part is necessary.
                print('Error!', ex)
                if connection is not None: await connection.disconnect()

        if not dt4261_active:
            await asyncio.sleep(0)

            device = aioble.Device(aioble.ADDR_PUBLIC, address_dt4261)
            connection = None
            try:
                print('Connecting to', device)
                connection = await device.connect(timeout_ms=5000)
                if connection.is_connected():
                    print('Connected.', connection)

                    service = await connection.service(_Z3210_UNKNOWN2_UUID)
                    characteristic = await service.characteristic(_Z3210_UNKNOWN2_CHAR1_UUID)
                    await characteristic.subscribe(indicate=True)

                    dt4261_task = asyncio.create_task(main_4261(connection, characteristic))
                    dt4261_active = True
            except asyncio.TimeoutError:
                print("Timeout during connection")
                if connection is not None: await connection.disconnect()
            except Exception as ex: # Not sure if this part is necessary.
                print('Error!', ex)
                if connection is not None: await connection.disconnect()

        await asyncio.sleep(5)

async def cancel_task(task):
    await asyncio.sleep(1)
    #print(f'Cancel {task}')
    if task is not None: task.cancel()

async def terminator():
    global stop

    while not stop:

        if sw(): # Check boot switch
            await asyncio.sleep_ms(500)
            if sw(): # If switch held
                stop = True
        await asyncio.sleep(1)

    await cancel_task(hr_task)
    await cancel_task(dt4261_task)

    await asyncio.sleep(3) # Pause 3 secs to prove it.
    print("End.")

async def start():

    main_tasks = asyncio.create_task(conn_multiple())
    terminator_task = asyncio.create_task(terminator())
    await asyncio.gather(main_tasks, terminator_task)

    await asyncio.sleep(1)

try:
    asyncio.run(start())
finally:
    asyncio.new_event_loop()  # Clear retained state

