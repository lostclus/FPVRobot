import struct
from collections import namedtuple

DEVICE_PING = 0
DEVICE_MOTOR_L = 1
DEVICE_MOTOR_R = 2
DEVICE_CAM_SERVO_H = 3
DEVICE_CAM_SERVO_V = 4
DEVICE_VOLAGE = 5

MESSAGE_MAGICK = b'c'
MessageTuple = namedtuple('MessageTuple', ['magick', 'device', 'value'])
message_struct = struct.Struct('<cBh')


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
    while True:
        if ser.in_waiting == 0:
            return None
        buffer = await ser.read_async(1)
        if buffer == MESSAGE_MAGICK:
            break
    buffer += await ser.read_async(message_size() - 1)
    msg = load_message(buffer)
    return msg


async def write_message(ser, msg):
    return await ser.write_async(dump_message(msg))
