import os

ARD1_PORT = os.getenv('ARD1_PORT', '/dev/serial0')
ARD1_BAUDRATE = int(os.getenv('ARD1_BAUDRATE', 9600))
ARD1_TIMEOUT = float(os.getenv('ARD1_TIMEOUT', 0.1))

DEFAULT_CAMERA_SIZE = tuple(
    [
        int(v)
        for v in os.getenv('DEFAULT_CAMERA_SIZE', '640x480').split('x')
    ]
)
DEFAULT_CAMERA_QUALITY = int(os.getenv('DEFAULT_CAMERA_QUALITY', 2))
CAMERA_TRANSFORM = {
    k: True
    for k in os.getenv('CAMERA_TRANSFORM', 'hflip,vflip').split(',')
}

AUTH_USER = os.getenv('AUTH_USER')
AUTH_PASSWORD = os.getenv('AUTH_PASSWORD')
