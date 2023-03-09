import asyncio
import struct
from collections import namedtuple
from contextlib import contextmanager

import aioserial

from .config import (
    MOTOR_SERVO_BAUDRATE,
    MOTOR_SERVO_PORT,
    MOTOR_SERVO_TIMEOUT,
)

DEVICE_PING = 0
DEVICE_MOTOR_L = 1
DEVICE_MOTOR_R = 2
DEVICE_CAM_SERVO_H = 3
DEVICE_CAM_SERVO_V = 4
DEVICE_CAM_SERVO_MOVE_H = 5
DEVICE_CAM_SERVO_MOVE_V = 6
DEVICE_VOLAGE = 7

MESSAGE_MAGICK = b'FpvB'
MessageTuple = namedtuple('MessageTuple', ['magick', 'device', 'value'])
message_struct = struct.Struct('<4shh')

write_lock = asyncio.Lock()


def load_message(buffer):
    msg = MessageTuple._make(message_struct.unpack(buffer))
    assert msg.magick == MESSAGE_MAGICK
    return msg


def dump_message(msg):
    assert msg.magick == MESSAGE_MAGICK
    return message_struct.pack(*msg)


def new_message(device, value):
    msg = MessageTuple(magick=MESSAGE_MAGICK, device=device, value=value)
    return msg


def message_size():
    return struct.calcsize(message_struct.format)


async def read_message(ser):
    buf = None
    while buf != MESSAGE_MAGICK:
        buf = await ser.read_async(len(MESSAGE_MAGICK))
    buf += await ser.read_async(message_size() - len(MESSAGE_MAGICK))
    msg = load_message(buf)
    return msg


async def write_message(ser, msg):
    async with write_lock:
        count = await ser.write_async(dump_message(msg))
    return count


async def write_value(ser, device, value):
    msg = new_message(device, value)
    return await write_message(ser, msg)


async def write_ping(ser):
    await write_value(ser, DEVICE_PING, 0)


async def messages_generator(ser):
    while True:
        msg = await read_message(ser)
        yield msg


async def process_messages(ser, app):
    async for msg in messages_generator(ser):
        if msg.device == DEVICE_VOLAGE:
            for ws in set(app['websockets']):
                data = {
                    'type': 'device',
                    'device': msg.device,
                    'value': msg.value,
                }
                await ws.send_json(data)


@contextmanager
def create_serial():
    with aioserial.AioSerial(
        MOTOR_SERVO_PORT,
        MOTOR_SERVO_BAUDRATE,
        timeout=MOTOR_SERVO_TIMEOUT,
    ) as ser:
        yield ser
