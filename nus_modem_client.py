# (c) 2024 ekspla.
# MIT License.  https://github.com/ekspla/micropython_aioble_examples
#
# An example pair of codes using YMODEM/Nordic UART Service.
# Requires micropython-lib/aioble after [commit 68e3e07](https://github.com/micropython/micropython-lib/commit/68e3e07bc7ab63931cead3854b2a114e9a084248)

import sys

sys.path.append('')

import machine
import asyncio
import aioble
import bluetooth
import os
import gc
from collections import deque
import time
from array import array


_TARGET_NAME = "mpy-nus"

_NUS_SERVICE_UUID = bluetooth.UUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
_NUS_RX_CHARACTERISTIC_UUID = bluetooth.UUID("6e400002-b5a3-f393-e0a9-e50e24dcca9e")
_NUS_TX_CHARACTERISTIC_UUID = bluetooth.UUID("6e400003-b5a3-f393-e0a9-e50e24dcca9e")

VALUE_SOH = bytearray([0x01])                             # SOH == 128-byte data
#VALUE_STX = bytearray([0x02])                             # STX == 1024-byte data
VALUE_C = bytearray([0x43])                               # 'C'
#VALUE_G = bytearray([0x47])                               # 'G'
VALUE_ACK = bytearray([0x06])                             # ACK
VALUE_NAK = bytearray([0x15])                             # NAK
VALUE_EOT = bytearray([0x04])                             # EOT
VALUE_CAN = bytearray([0x18])                             # CAN

AWAIT_NEW_DATA = bytearray(b'AwaitNewData')

class NUSModemClient:
    def __init__(self):
        #self.lock = asyncio.Lock()
        self.ctl_characteristic = None
        self.tx_characteristic = None
        self.rx_characteristic = None
        # **Packet**
        self.notification_data = bytearray()
        # **Block**
        self.is_block = False
        self.block_data_size = 128
        self.block_buf = bytearray(3 + self.block_data_size + 2)               # Header(SOH, num, ~num); data; CRC16
        self.block_num = 0 # Block number(0-255).
        self.idx_block_buf = 0 # Index in block_buf.
        self.mv_block_buf = memoryview(self.block_buf)
        self.block_data = self.mv_block_buf[3:-2]
        self.block_crc = self.mv_block_buf[-2:]
        self.block_error = False
        # **File**                                                               A file is made of blocks; a block is made of packets.
        self.data_size = 0
        self.data_written = 0
        self.filename = ''
        self.is_write_mode = False
        self.write_buf = bytearray(self.block_data_size * 4)
        self.mv_write_buf = memoryview(self.write_buf)
        self.write_buf_page = tuple(self.mv_write_buf[i*self.block_data_size:(i+1)*self.block_data_size] for i in range(4))
        self.idx_write_buf = 0

    async def notify_handler(self):
        _EOT = bytes(VALUE_EOT)
        queue = self.tx_characteristic._notify_queue

        def append_to_block_buf(data):
            if (len_data := len(data)):
                self.block_buf[self.idx_block_buf:self.idx_block_buf + len_data] = data
                self.idx_block_buf += len_data

        async def fill_queue(n, timeout_ms):
            async def q():
                while len(queue) < n:
                    #await asyncio.sleep_ms(10)
                    await asyncio.sleep_ms(2)
            try:
                await asyncio.wait_for_ms(q(), timeout_ms)
            except asyncio.TimeoutError:
                pass

        while True:
            data = await self.tx_characteristic.notified()
            if data == _EOT:                                                         # Receive EOT.
                self.is_block = False
                self.notification_data[:] = data
            elif self.is_block:                                                     # Packets should be combined to make a block.
                await fill_queue(n=6, timeout_ms=150)
                append_to_block_buf(data)
                while len(queue) >= 1:
                    append_to_block_buf(queue.popleft())
                self.tx_characteristic._notify_event.clear()                        # Make sure to clear the flag.
            else:
                self.notification_data[:] = data                                    # Other messages/responses.
            await asyncio.sleep(0)

    async def clear_notify_queue(self):
        queue = self.tx_characteristic._notify_queue
        await asyncio.sleep_ms(200)
        while len(queue) >= 1:
            _ = queue.popleft()
        self.tx_characteristic._notify_event.clear()                                # Make sure to clear the flag.

    async def discover_device(self, target_name):
        # Scan for 20 seconds, in active mode, with very low interval/window (to maximise detection rate).
        async with aioble.scan(duration_ms=20_000, interval_us=30000, window_us=30000, active=True) as scanner:
            async for result in scanner:
                # See if it matches target_name.
                if (name := result.name()) is not None and target_name in name:
                    print(f"Found target device: {name} - {result.device}")
                    return result.device

        print(f"Device with name {target_name} not found.")
        return None

    async def send_cmd(self, char, value, delay_ms):
        try:
            await char.write(value, False)
        except Exception as e:
            print(f"Failed to write value to characteristic: {e}")
        await asyncio.sleep_ms(delay_ms)

    async def read_block_zero(self):
        self.block_num = -1
        self.idx_block_buf = 0
        self.is_block = True
        self.block_error = False
        await self.send_cmd(self.rx_characteristic, VALUE_C, 100)                     # Send 'C'.
        await self.read_block()

    async def read_block(self):
        # [ESP32] A cleaner implementation with asyncio.Event() than this polling function lead to a decreased throughput.
        async def check_block_buf():
            while self.is_block and self.idx_block_buf < 133: # c.f. 1+1+1+128+2=133 bytes (one block)
                #await asyncio.sleep_ms(10)
                await asyncio.sleep_ms(2)

        def write_to_buf(data):
            self.write_buf_page[self.idx_write_buf][:] = data
            self.idx_write_buf += 1
            if self.idx_write_buf == 4:
                self.save_chunk_raw(self.write_buf)
                self.idx_write_buf = 0
            elif (self.data_written + self.block_data_size) == self.data_size:
                flush_write_buf()
            return self.block_data_size

        def flush_write_buf():
            self.save_chunk_raw(self.mv_write_buf[:self.idx_write_buf * self.block_data_size])
            self.idx_write_buf = 0

        try:
            await asyncio.wait_for(check_block_buf(), timeout=5) # Set client/server timeouts at 5/10 sec.
            if not self.is_block: return # The 1st EOT may arrive very late.
            if int.from_bytes(self.block_crc, 'big') != self.crc16_arc(self.block_data):
                self.block_error = True
                print(f'Size: {self.idx_block_buf}')
                print(self.block_buf)
            else:
                if self.is_write_mode:                                                    # Blocks should be combined to make a file.
                    if (self.data_written + self.block_data_size) <= self.data_size:
                        self.data_written += write_to_buf(self.block_data)
                    else:
                        if self.idx_write_buf > 0: flush_write_buf()
                        mv_block_data = memoryview(self.block_data)
                        i = -1
                        while self.block_data[i] == 0x00: # Remove padded zeros at the end.
                            i -= 1
                        self.data_written += self.save_chunk_raw(mv_block_data[:i+1])
                if self.block_buf[1] == (self.block_num + 1) % 256:
                    if self.block_error: print(f'Fixed error in block{self.block_buf[1]}.')
                else:
                    print(f'Unexpected block: {self.block_num} -> {self.block_buf[1]}')
                self.block_num = self.block_buf[1]
                self.block_error = False
        except asyncio.TimeoutError:
            self.block_error = True
            print('Timeout 5 sec.')
        # Prepare for the next data block.
        self.idx_block_buf = 0

    async def end_of_transfer(self):
        # The first EOT was received already.
        await asyncio.sleep_ms(100) # This avoids NAK to be sent too fast.
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(self.rx_characteristic, VALUE_NAK, 100) # Send NAK.
        await self.wait_until_data(self.tx_characteristic)                                   # Receive the second EOT.
        await asyncio.sleep_ms(100) # This avoids ACK to be sent too fast.
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(self.rx_characteristic, VALUE_ACK, 100) # Send ACK.

    async def fetch_file(self):
        self.notification_data = AWAIT_NEW_DATA

        self.is_write_mode = False                                                         # Do not write block 0
        notify_handler_task = asyncio.create_task(self.notify_handler())
        await asyncio.sleep(1)
        retries = 3
        while retries > 0:
            await self.read_block_zero() # Block 0 consists of name and size of the file.
            if self.block_error:
                retries -= 1
                await self.clear_notify_queue()
                await self.send_cmd(self.rx_characteristic, VALUE_NAK, 100)               # Send NAK on error.
            else:
                break
        if retries == 0: # Too many errors in reading block zero; cancel transport.
            await self.send_cmd(self.rx_characteristic, VALUE_CAN, 100)                   # Send CAN (cancel).
            notify_handler_task.cancel()
            return

        file_informations = bytes(self.block_data).rstrip(b'\x00').decode('utf-8').split()
        self.filename = file_informations[0]
        self.data_size = int(file_informations[1])
        if self.filename in os.listdir('/sd'):
            os.rename(f'/sd/{self.filename}', f'/sd/{self.filename}.old')

        print(time.localtime())
        await self.send_cmd(self.rx_characteristic, VALUE_ACK, 100)                       # Send ACK.
        await self.send_cmd(self.rx_characteristic, VALUE_C, 100)                         # Send 'C'.

        # Blocks of num>=1 should be combined to obtain the file.
        self.is_write_mode = True
        self.data_written = 0
        self.idx_write_buf = 0
        while self.is_block:                                                              # Receive EOT to exit this loop.
            await self.read_block()
            if not self.is_block: break # The 1st EOT may arrive very late.
            if self.block_num % 128 == 0: gc.collect()
            if self.block_error:
                await self.clear_notify_queue()
                #await self.send_cmd(self.rx_characteristic, VALUE_NAK, 10)               # Send NAK on error.
                await self.send_cmd(self.rx_characteristic, VALUE_NAK, 2)               # Send NAK on error.
            else:
                #await self.send_cmd(self.rx_characteristic, VALUE_ACK, 10)               # Send ACK.
                await self.send_cmd(self.rx_characteristic, VALUE_ACK, 2)               # Send ACK.
        notify_handler_task.cancel()
        await self.end_of_transfer()
        if self.data_written != self.data_size:
            print(f"Error: {self.data_written}(file size) != {self.data_size}(spec)")
        else:
            print(f"Successfully wrote combined data to {self.filename}")
        print(time.localtime())

    async def wait_until_data(self, char):
        try:
            self.notification_data[:] = await char.notified(timeout_ms=10_000)
        except asyncio.TimeoutError:
                print(f"Something went wrong. No new notification data.")

    async def main(self):
        device = await self.discover_device(_TARGET_NAME)
        if not device:
            print(f"{_TARGET_NAME} not found")
            return

        try:
            print("Connecting to", device)
            connection = await device.connect(
                timeout_ms=60_000, 
                scan_duration_ms=5_000, min_conn_interval_us=7_500, max_conn_interval_us=7_500)
        except asyncio.TimeoutError:
            print("Timeout during connection")
            return

        async with connection:
            try:
                nus_service = await connection.service(_NUS_SERVICE_UUID)
                # Client (Central) -> Server (Peripheral)
                self.rx_characteristic = await nus_service.characteristic(_NUS_RX_CHARACTERISTIC_UUID)
                # Server (Peripheral) -> Client (Central)
                self.tx_characteristic = await nus_service.characteristic(_NUS_TX_CHARACTERISTIC_UUID)
                self.tx_characteristic._notify_queue = deque((), 7)
                await self.tx_characteristic.subscribe(notify=True)
            except asyncio.TimeoutError:
                print("Timeout discovering services/characteristics")
                return

            await self.fetch_file()

    def save_chunk_raw(self, data):
        with open(f'/sd/{self.filename}', 'ab') as f:
            return f.write(data)

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
    import os, machine
    if not "sd" in os.listdir():
        try:
            #sdcard = machine.SDCard(slot=2, freq=40_000_000)
            #os.mount(sdcard, "/sd")
            import sdcard
            from machine import Pin
            spi = machine.SPI(2, sck=Pin(12), mosi=Pin(11), miso=Pin(13))
            sd = sdcard.SDCard(spi, Pin(10), 40_000_000)
            os.mount(sd, '/sd')
        except:
            del sdcard
            print("No sdcard")
            sys.exit()

    freq = machine.freq()
    machine.freq(240_000_000)
    client = NUSModemClient()
    try:
        asyncio.run(client.main())
    finally:
        asyncio.new_event_loop() # Clear retained state.
        machine.freq(freq)
