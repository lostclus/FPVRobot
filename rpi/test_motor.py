import itertools
import struct
import sys
import time
from collections import namedtuple

import serial

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


def read_message(ser):
    if ser.in_waiting < message_size():
        return None
    buffer = ser.read(len(MESSAGE_MAGICK))
    if buffer != MESSAGE_MAGICK:
        return None
    buffer += ser.read(message_size() - len(MESSAGE_MAGICK))
    msg = load_message(buffer)
    return msg


def write_message(ser, msg):
    count = ser.write(dump_message(msg))
    print(msg.device, msg.value, count)
    return count


def write_value(ser, device, value):
    msg = new_message(device=device, value=value)
    return write_message(ser, msg)


def test_motors(ser):
    for device in (DEVICE_MOTOR_L, DEVICE_MOTOR_R):
        for value in itertools.chain(
            range(0, 256, 8),
            range(255, 0, -8),
            range(0, -256, -8),
            range(-255, 0, 8),
        ):
            write_value(ser, device, value)
            time.sleep(0.1)


def test_servos(ser):
    for device in (DEVICE_CAM_SERVO_H, DEVICE_CAM_SERVO_V):
        for value in itertools.chain(
            range(90, 176, 1),
            range(175, 90, -1),
            range(90, 5, -1),
            range(5, 90, 1),
        ):
            write_value(ser, device, value)
            time.sleep(0.02)


def test_servos_move(ser):
    for device in (DEVICE_CAM_SERVO_MOVE_H, DEVICE_CAM_SERVO_MOVE_V):
        for value in (1, -1, 0):
            write_value(ser, device, value)
            if value == 0:
                time.sleep(1)
            else:
                time.sleep(5)


def test_voltage(ser):
    for count in range(10):
        write_value(ser, DEVICE_VOLAGE, 0)
        for i in range(10):
            msg = read_message(ser)
            if msg is not None:
                break
            time.sleep(0.01)
        print(DEVICE_VOLAGE, msg)


def main(argv):
    with serial.Serial(argv[1], 9600, timeout=0.1) as ser:
        time.sleep(0.5)
        write_value(ser, 0, 0)
        test_motors(ser)
        #test_servos(ser)
        test_servos_move(ser)
        test_voltage(ser)


if __name__ == '__main__':
    main(sys.argv)
