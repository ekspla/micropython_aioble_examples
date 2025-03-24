# (c) 2024 ekspla.
# MIT License.  https://github.com/ekspla/micropython_aioble_examples
#
# An example pair of codes using YMODEM/Nordic UART Service.

import sys

sys.path.append('')

from micropython import const

import machine
import os
import asyncio
import aioble
import bluetooth
from array import array

_NUS_SERVICE_UUID = bluetooth.UUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
_NUS_RX_CHARACTERISTIC_UUID = bluetooth.UUID("6e400002-b5a3-f393-e0a9-e50e24dcca9e")
_NUS_TX_CHARACTERISTIC_UUID = bluetooth.UUID("6e400003-b5a3-f393-e0a9-e50e24dcca9e")
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)

# How frequently to send advertising beacons.
_ADV_INTERVAL_US = const(250_000)

VALUE_SOH = bytearray([0x01])                             # SOH == 128-byte data
VALUE_STX = bytearray([0x02])                             # STX == 1024-byte data
VALUE_C = bytearray([0x43])                               # 'C'
#VALUE_G = bytearray([0x47])                               # 'G'
VALUE_ACK = bytearray([0x06])                             # ACK
VALUE_NAK = bytearray([0x15])                             # NAK
VALUE_EOT = bytearray([0x04])                             # EOT
VALUE_CAN = bytearray([0x18])                             # CAN

##_FILEPATH = '/sd/test.bin'
_FILEPATH = 'test.bin'

class NUSModemServer:
    def __init__(self):
        # Register GATT server.
        nus_service = aioble.Service(_NUS_SERVICE_UUID)
        # Client (Central) -> Server (Peripheral)
        self.rx_characteristic = aioble.Characteristic(
            nus_service, _NUS_RX_CHARACTERISTIC_UUID, write=True, write_no_response=True, 
            capture=True, 
        )
        # Server (Peripheral) -> Client (Central)
        self.tx_characteristic = aioble.BufferedCharacteristic(
            nus_service, _NUS_TX_CHARACTERISTIC_UUID, notify=True, 
            max_len=20, 
        )
        aioble.register_services(nus_service)
        aioble.config(mtu=512)
        # **Packet**
        self.mtu_size = 23
        # **Block**
        self.use_stx = False # True/False = STX/SOH
        self.block_buf = bytearray(3 + 1024 + 2)                                 # Header(SOH/STX, num, ~num); data(128 or 1024 bytes); CRC16
        self.block_num = 0 # Block number(0-255).
        #self.idx_block_buf = 0 # Index in block_buf.
        self.mv_block_buf = memoryview(self.block_buf)
        self.block_size = None
        self.block_data = None
        self.block_crc = None
        self.block_size_data_crc = (
            (3 + 128 + 2, self.mv_block_buf[3:131], self.mv_block_buf[131:133], ), # SOH
            (3 + 1024 + 2, self.mv_block_buf[3:-2], self.mv_block_buf[-2:], ),     # STX
        )
        # **File** A file is made of blocks; a block is made of packets.
        self.data_size = 0
        self.data_read = 0
        self.filename = ''

    def construct_block_zero(self):
        self.block_num = -1
        self.data_size = os.stat(_FILEPATH)[6]
        ##filename = _FILEPATH.split('/')[-1]
        filename = _FILEPATH
        header = bytes(f'{filename} {self.data_size}', 'utf-8')
        self.block_data[:len(header)] = header
        self.construct_block(len(header))

    def construct_block(self, nbytes):
        block_data_size = self.block_size - 5
        while nbytes < block_data_size:
            self.block_data[nbytes] = 0x00 # Zero padding to the end.
            nbytes += 1

        self.block_num = (self.block_num + 1) % 256
        self.block_buf[0] = VALUE_STX[0] if self.use_stx else VALUE_SOH[0]
        self.block_buf[1] = self.block_num
        self.block_buf[2] = 0xFF ^ self.block_num
        self.block_crc[:] = self.crc16_arc(self.block_data).to_bytes(2, 'big')

    async def send_block(self, char, delay_ms): # Send a block through packets.
        mtu = self.mtu_size - 3
        idx = 0
        n = self.block_size - mtu
        while idx < n:
            char.notify(self.connection, self.mv_block_buf[idx:(idx := idx + mtu)])
            await asyncio.sleep_ms(0)
        char.notify(self.connection, self.mv_block_buf[idx:self.block_size])
        await asyncio.sleep_ms(delay_ms)

    async def wait_until_data(self, char, t_ms=10_000):
        try:
            _, data = await char.written(timeout_ms=t_ms)
            return data
        except asyncio.TimeoutError:
            print(f"Something went wrong. No new data received.")
            sys.exit()
            ##await self.connection.disconnect()

    async def main(self):
        while True:
            async with await aioble.advertise(
                _ADV_INTERVAL_US,
                name="mpy-nus",
                services=[_NUS_SERVICE_UUID],
                appearance=_ADV_APPEARANCE_GENERIC_COMPUTER,
            ) as connection:
                print("Connection from", connection.device)
                self.connection = connection

                print("Waiting for 'C'.")
                # Receive 'C'.
                if await self.wait_until_data(self.rx_characteristic) != bytes(VALUE_C):
                    await self.connection.disconnect()
                else:
                    print("'C' was received.")

                # Check MTU
                self.mtu_size = self.connection.mtu or self.mtu_size
                print(f"MTU: {self.mtu_size}")

                # Send block number zero.  Receive ACK.
                self.use_stx = False # Always use SOH for block zero.
                self.block_size, self.block_data, self.block_crc = self.block_size_data_crc[int(self.use_stx)]
                self.construct_block_zero()
                retries = 3
                while retries > 0:
                    await self.send_block(self.tx_characteristic, delay_ms=5)
                    if await self.wait_until_data(self.rx_characteristic) == bytes(VALUE_ACK):
                        break
                    retries -= 1
                if retries == 0: # Too many errors; cancel transport.
                    print("Too many errors.")
                    #await self.connection.disconnect()
                    sys.exit()

                # Receive 'C'.
                if await self.wait_until_data(self.rx_characteristic) != bytes(VALUE_C):
                    await self.connection.disconnect()
                else:
                    print("The second 'C' was received.")

                # Send blocks of number >= 1
                self.use_stx = True if self.mtu_size > 23 else False
                self.block_size, self.block_data, self.block_crc = self.block_size_data_crc[int(self.use_stx)]
                self.data_read = 0
                with open(_FILEPATH, 'rb') as f:
                    while self.connection.is_connected():
                        if (nbytes := f.readinto(self.block_data)):
                            self.construct_block(nbytes)
                            self.data_read += nbytes
                            while True:
                                await self.send_block(self.tx_characteristic, delay_ms=5)
                                if await self.wait_until_data(self.rx_characteristic) == bytes(VALUE_ACK):
                                    break
                        else:
                            # Send EOT
                            self.tx_characteristic.notify(self.connection, VALUE_EOT)
                            # Receive NAK
                            if await self.wait_until_data(self.rx_characteristic) != bytes(VALUE_NAK):
                                await self.connection.disconnect()
                            # Send EOT
                            self.tx_characteristic.notify(self.connection, VALUE_EOT)
                            # Receive ACK
                            if await self.wait_until_data(self.rx_characteristic) != bytes(VALUE_ACK):
                                await self.connection.disconnect()
                            print('File transmission finished.')
                            print(f'File size: {self.data_size}.  Transmitted size: {self.data_read}.')
                            await self.connection.disconnect()
                print("Disconnected.")
                self.mtu_size = 23

    @micropython.viper
    def crc16_arc(self, byte_array) -> int:
        '''crc16/arc
        XOSS uses CRC16/ARC instead of CRC16/XMODEM.
        '''
        crc: int = 0
        data = ptr8(byte_array)
        length = int(len(byte_array))
        table = ptr16(CRC16_ARC_TBL)
        i: int = 0
        while i < length:
            crc = (crc >> 8) ^ table[(crc ^ data[i]) & 0xff]
            i += 1
        return crc

CRC16_ARC_TBL = array("H", (
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
    0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
    0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
    0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
    0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
    0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
    0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
    0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
    0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
    0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
    0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
    0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
    0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
    0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
    0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
    0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
    0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
    0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
    0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
    0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
    0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
    0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
    0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
    0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
    0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
    0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
    0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
    0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
    0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040,
    ))

def start():
    #freq = machine.freq()
    #machine.freq(240_000_000)
    server = NUSModemServer()
    try:
        asyncio.run(server.main())
    finally:
        asyncio.new_event_loop() # Clear retained state.
        #machine.freq(freq)
