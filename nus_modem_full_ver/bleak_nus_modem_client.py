#!/usr/bin/env python
#coding:utf-8
#
# (c) 2024-2025 ekspla.
# MIT License.  https://github.com/ekspla/micropython_aioble_examples
#
# An example client code of CPython/Bleak using YMODEM/Nordic UART Service.
# Requires [Bleak](https://github.com/hbldh/bleak/).

import asyncio
from bleak import BleakScanner, BleakClient
import os
import time
import datetime
import platform

TARGET_NAME = "mpy-nus"
#SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
TX_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
RX_CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

VALUE_SOH = bytearray([0x01])                             # SOH == 128-byte data
VALUE_STX = bytearray([0x02])                             # STX == 1024-byte data
VALUE_C = bytearray([0x43])                               # 'C'
#VALUE_G = bytearray([0x47])                               # 'G'
VALUE_ACK = bytearray([0x06])                             # ACK
VALUE_NAK = bytearray([0x15])                             # NAK
VALUE_EOT = bytearray([0x04])                             # EOT
VALUE_CAN = bytearray([0x18])                             # CAN

AWAIT_NEW_DATA = bytearray(b'AwaitNewData')

class NUSModemClient:
    def __init__(self):
        self.lock = asyncio.Lock()
        # **Packet**
        self.notification_data = bytearray()
        self.mtu_size = 23
        # **Block**
        self.block_buf = bytearray(3 + 1024 + 2)                                 # Header(SOH/STX, num, ~num); data(128 or 1024 bytes); CRC16
        self.block_num = 0 # Block number(0-255).
        self.idx_block_buf = 0 # Index in block_buf.
        self.mv_block_buf = memoryview(self.block_buf)
        self.block_size = None
        self.block_data = None
        self.block_crc = None
        self.block_size_data_crc = (
            (3 + 128 + 2, self.mv_block_buf[3:131], self.mv_block_buf[131:133], ), # SOH
            (3 + 1024 + 2, self.mv_block_buf[3:-2], self.mv_block_buf[-2:], ),     # STX
        )
        self.block_error = False
        # **File**                                                               A file is made of blocks; a block is made of packets.
        self.data = bytearray()
        self.data_size = 0
        self.filename = ''
        self.is_download = False

    def create_notification_handler(self):
        async def notification_handler(sender, data):
            ##print(data) # For test.
            if data == VALUE_EOT:                                               # Receive EOT.
                self.is_download = False
                self.notification_data = data
            elif self.is_download:                                              # Packets should be combined to make a block.
                async with self.lock: # Use asyncio.Lock() for safety.
                    self.mv_block_buf[self.idx_block_buf:self.idx_block_buf + (len_data := len(data))] = data
                    self.idx_block_buf += len_data
            else:
                self.notification_data = data                                   # Other messages/responses.

        return notification_handler

    async def discover_device(self, target_name):
        print("Scanning for Bluetooth devices...")
        retries = 3
        while retries > 0:
            devices = await BleakScanner.discover(timeout=30.0)

            for device in devices:
                print(f"Found device: {device.name} - {device.address}")
                if device.name is not None and target_name in device.name:
                    print(f"Found target device: {device.name} - {device.address}")
                    return device
            retries -= 1

        print(f"Device with name {target_name} not found.")
        return None

    async def start_notify(self, client, uuid):
        try:
            await client.start_notify(uuid, self.create_notification_handler())
        except Exception as e:
            print(f"Failed to start notifications: {e}")

    async def send_cmd(self, client, uuid, value, delay):
        try:
            ##print(value) # For test.
            await client.write_gatt_char(uuid, value, False)
        except Exception as e:
            print(f"Failed to write value to characteristic: {e}")
        await asyncio.sleep(delay)

    async def read_block_zero(self, client):
        self.block_num = -1
        self.idx_block_buf = 0
        self.is_download = True
        self.block_error = False
        await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_C, 0.1)      # Send 'C'.
        await self.read_block(client)

    async def read_block(self, client):
        #_SOH = VALUE_SOH[0] # SOH == 128-byte data
        _STX = VALUE_STX[0] # STX == 1024-byte data
        async def check_block_buf():
            while self.is_download and self.idx_block_buf == 0:
                await asyncio.sleep(0.01)
            if not self.is_download: return
            self.block_size, self.block_data, self.block_crc = self.block_size_data_crc[int(self.block_buf[0] == _STX)]
            while self.idx_block_buf < self.block_size:
                await asyncio.sleep(0.01)

        try:
            await asyncio.wait_for(check_block_buf(), timeout=10)
            if not self.is_download: return # The 1st EOT may arrive very late.
            if int.from_bytes(self.block_crc, 'big') != self.crc16_arc(self.block_data):
                self.block_error = True
                print(f'Size: {self.idx_block_buf}')
            else:
                self.data.extend(self.block_data)                                # Blocks should be combined to make a file.
                if self.block_buf[1] == (self.block_num + 1) % 256:
                    if self.block_error: print(f'Fixed error in block{self.block_buf[1]}.')
                else:
                    print(f'Unexpected block: {self.block_num} -> {self.block_buf[1]}')
                self.block_num = self.block_buf[1]
                self.block_error = False
        except asyncio.TimeoutError:
            self.block_error = True
            print('Timeout 10 sec.')
        # Prepare for the next data block.
        self.idx_block_buf = 0

    async def end_of_transfer(self, client):
        # The first EOT was received already.
        await asyncio.sleep(0.1) # This avoids NAK to be sent too fast.
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_NAK, 0.01) # Send NAK.
        await self.wait_until_data(client)                                   # Receive the second EOT.
        await asyncio.sleep(0.1) # This avoids ACK to be sent too fast.
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_ACK, 0.01) # Send ACK.

    async def fetch_file(self, client):
        self.notification_data = AWAIT_NEW_DATA

        retries = 3
        while retries > 0:
            await self.read_block_zero(client) # Block 0 consists of name and size of the file.
            if self.block_error:
                retries -= 1
                self.is_download = False # Wait 0.2 s for garbage.
                await asyncio.sleep(0.2)
                self.is_download = True
                await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_NAK, 0.1) # Send NAK on error.
            else:
                break
        if retries == 0: # Too many errors in reading block zero; cancel transport.
            await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_CAN, 0.1)    # Send CAN (cancel).
            return

        file_informations = self.block_data.tobytes().rstrip(b'\x00').decode('utf-8').split()
        self.filename = file_informations[0]
        self.data_size = int(file_informations[1])
        if os.path.exists(self.filename):
            os.replace(f'{self.filename}', f'{self.filename}.old')
        self.data = bytearray() # Where the file to be stored.

        print(time.asctime())
        await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_ACK, 0.1)       # Send ACK.
        await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_C, 0.1)         # Send 'C'.

        # Blocks of num>=1 should be combined to obtain the file.
        while self.is_download:                                                       # Receive EOT to exit this loop.
            await self.read_block(client)
            if not self.is_download: break # The 1st EOT may arrive very late.
            if self.block_error:
                self.is_download = False # Wait 0.2 s for garbage.
                await asyncio.sleep(0.2)
                self.is_download = True
                await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_NAK, 0.01) # Send NAK on error.
            else:
                await self.send_cmd(client, RX_CHARACTERISTIC_UUID, VALUE_ACK, 0.01) # Send ACK.
        await self.end_of_transfer(client)
        self.save_file_raw(self.filename)
        print(time.asctime())

    async def wait_until_data(self, client):
        i = 0
        while self.notification_data == AWAIT_NEW_DATA:
            await asyncio.sleep(0.01)
            i = i + 1
            if i >= 1000:
                print(f"Something went wrong. No new notification data.")
                break

    async def main(self):
        device = await self.discover_device(TARGET_NAME)
        if not device:
            print(f"{TARGET_NAME} not found")
            return

        async with BleakClient(device.address, timeout=60.0) as client:
            if client.is_connected:
                print(f"Connected to {device.name}")
                await asyncio.sleep(2)

                # For BlueZ >= 5.62
                # BlueZ doesn't have a proper way to get the MTU, so we have this hack.
                # If this doesn't work for you, you can set the client._mtu_size attribute
                # to override the value instead.
                #if client._backend.__class__.__name__ == "BleakClientBlueZDBus":
                #    await client._backend._acquire_mtu()

                print(f"MTU {client.mtu_size}")
                self.mtu_size = client.mtu_size

                await self.start_notify(client, TX_CHARACTERISTIC_UUID) # Notifications are stopped automatically on disconnect.
                print(f"Notifications started")

                # https://gist.github.com/ndeadly/7d27aa63e2f653a902a2474dbcbc08b3
                # Set better connection parameters on Windows 11 where the API supports it
                if platform.system() == 'Windows':
                    version = platform.version()
                    build_number = int(version.split('.')[-1])
                    if build_number >= 22000:
                        from bleak.backends.winrt.client import BleakClientWinRT
                        from winrt.windows.devices.bluetooth import BluetoothLEPreferredConnectionParameters
                        if isinstance(backend := client._backend, BleakClientWinRT):
                            print('Requesting to change connection parameters...')
                            backend._requester.request_preferred_connection_parameters(
                                BluetoothLEPreferredConnectionParameters.throughput_optimized
                                #BluetoothLEPreferredConnectionParameters.balanced
                                #BluetoothLEPreferredConnectionParameters.power_optimized
                            )
                            await asyncio.sleep(1) # Wait for the request to be applied.
                            print('Done.')

                await self.fetch_file(client)

            else:
                print(f"Failed to connect to {device.name}")

    def save_file_raw(self, filename):
        mv_file_data = memoryview(self.data)
        i = -1
        while self.data[i] == 0x00: # Remove padded zeros at the end.
            i -= 1

        with open(filename, "wb") as file:
            size = file.write(mv_file_data[:i+1] if i < -1 else self.data)
        if size != self.data_size:
            print(f"Error: {size}(file size) != {self.data_size}(spec)")
        else:
            print(f"Successfully wrote combined data to {filename}")

    def crc16_arc(self, data):
        '''crc16/arc
        XOSS uses CRC16/ARC instead of CRC16/XMODEM.
        '''
        crc = 0
        for x in data:
            crc ^= x
            for _ in range(8):
                if (crc & 0x0001) > 0:
                    crc = (crc >> 1) ^ 0xa001
                else:
                    crc = crc >> 1
        return crc & 0xffff

if __name__ == "__main__":
    client = NUSModemClient()
    try:
        asyncio.run(client.main())
    finally:
        asyncio.new_event_loop() # Clear retained state.
