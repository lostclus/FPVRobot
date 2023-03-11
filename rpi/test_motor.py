import itertools
import struct
import sys
import time
from collections import namedtuple

import serial

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


def load_response(buffer):
    response = ResponseTuple._make(response_struct.unpack(buffer))
    assert response.magick == MAGICK
    return response


def dump_request(request):
    assert request.magick == MAGICK
    return request_struct.pack(*request)


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


def read_response(ser):
    size = response_size()
    if ser.in_waiting < size:
        return None
    buffer = ser.read(len(MAGICK))
    if buffer != MAGICK:
        return None
    buffer += ser.read(size - len(MAGICK))
    response = load_response(buffer)
    return response


def write_request(ser, request):
    count = ser.write(dump_request(request))
    print(request, count)
    return count


def test_motors(ser):
    for device in ('motor_l', 'motor_r'):
        for value in itertools.chain(
            range(0, 256, 8),
            range(255, 0, -8),
            range(0, -256, -8),
            range(-255, 0, 8),
        ):
            request = new_requset(**{device: value})
            write_request(ser, request)
            time.sleep(0.1)


def test_servos(ser):
    for device in ('cam_servo_h', 'cam_servo_v'):
        for value in itertools.chain(
            range(90, 176, 1),
            range(175, 90, -1),
            range(90, 5, -1),
            range(5, 90, 1),
        ):
            request = new_requset(**{device: CAM_SERVO_POS_BASE + value})
            write_request(ser, request)
            time.sleep(0.02)


def test_servos_move(ser):
    for device in ('cam_servo_h', 'cam_servo_v'):
        for value in (1, -1, 0):
            for i in range(value == 0 and 1 or 10):
                request = new_requset(**{device: value})
                write_request(ser, request)
                time.sleep(0.5)


def test_lighting(ser):
    for value in range(8):
        request = new_requset(lighting=value)
        write_request(ser, request)
        time.sleep(1)


def test_voltage(ser):
    time.sleep(0.5)
    while read_response(ser) is not None:
        pass
    for count in range(5):
        write_request(ser, new_requset())
        for i in range(10):
            response = read_response(ser)
            if response is not None:
                break
            time.sleep(0.01)
        print(response)


def main(argv):
    with serial.Serial(argv[1], 9600, timeout=0.1) as ser:
        time.sleep(0.5)
        write_request(ser, new_requset())
        test_motors(ser)
        #test_servos(ser)
        test_servos_move(ser)
        test_lighting(ser)
        test_voltage(ser)


if __name__ == '__main__':
    main(sys.argv)
