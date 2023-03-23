import asyncio
import struct
from collections import namedtuple
from contextlib import contextmanager

import aioserial

from .config import (
    ARD1_BAUDRATE,
    ARD1_PORT,
    ARD1_TIMEOUT,
)

MAGICK = b'FpvB'
RequestTuple = namedtuple(
    'RequestTuple', [
        'magick',
        'motor_l',
        'motor_r',
        'cam_servo_h',
        'cam_servo_v',
        'lighting',
    ],
)
request_struct = struct.Struct('<4s5h')

ResponseTuple = namedtuple(
    'ResponseTuple', [
        'magick',
        'cam_servo_h',
        'cam_servo_v',
        'voltage',
    ],
)
response_struct = struct.Struct('<4s3h')

CAM_SERVO_POS_BASE = 1000

write_lock = asyncio.Lock()


def load_response(buffer):
    response = ResponseTuple._make(response_struct.unpack(buffer))
    assert response.magick == MAGICK
    return response


def dump_request(request):
    assert request.magick == MAGICK
    return request_struct.pack(*request)


def response_as_dict(response):
    d = response._asdict()
    d.pop('magick')
    return d


def new_requset(**kwargs):
    kwargs.setdefault('motor_l', 0)
    kwargs.setdefault('motor_r', 0)
    kwargs.setdefault('cam_servo_h', 0)
    kwargs.setdefault('cam_servo_v', 0)
    kwargs.setdefault('lighting', 0)
    request = RequestTuple(magick=MAGICK, **kwargs)
    return request


def request_size():
    return struct.calcsize(request_struct.format)


def response_size():
    return struct.calcsize(response_struct.format)


async def read_response(ser):
    buf = None
    while buf != MAGICK:
        buf = await ser.read_async(len(MAGICK))
    buf += await ser.read_async(response_size() - len(MAGICK))
    response = load_response(buf)
    return response


async def write_request(ser, request):
    async with write_lock:
        count = await ser.write_async(dump_request(request))
    #print(request, count)
    return count


async def process_responses(ser, app):
    while True:
        response = await read_response(ser)
        for ws in set(app['websockets']):
            resp_data = response_as_dict(response)
            await ws.send_json(resp_data)


@contextmanager
def create_serial():
    with aioserial.AioSerial(
        ARD1_PORT,
        ARD1_BAUDRATE,
        timeout=ARD1_TIMEOUT,
    ) as ser:
        yield ser
