import io
import threading

from libcamera import controls, Transform
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput

from .config import (
    CAMERA_TRANSFORM,
    DEFAULT_CAMERA_QUALITY,
    DEFAULT_CAMERA_SIZE,
)

INT_TO_QUALITY = {
    0: Quality.VERY_LOW,
    1: Quality.LOW,
    2: Quality.MEDIUM,
    3: Quality.HIGH,
    4: Quality.VERY_HIGH,
}

QUALITY_TO_INT = {
    q: i for i, q in INT_TO_QUALITY.items()
}


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

    def get_frame(self):
        with self.condition:
            self.condition.wait()
            return self.frame


def create_camera():
    cam = Picamera2()
    cam.configure(
        cam.create_video_configuration(
            main={'size': DEFAULT_CAMERA_SIZE},
            transform=Transform(**CAMERA_TRANSFORM),
        )
    )
    cam._fpv_size = DEFAULT_CAMERA_SIZE
    cam._fpv_quality = INT_TO_QUALITY[DEFAULT_CAMERA_QUALITY]
    cam.set_controls({'AwbEnable': True})
    output = StreamingOutput()
    return (cam, output)


def start_camera(cam, output):
    quality = getattr(cam, '_fpv_quality', Quality.MEDIUM)
    cam.start_recording(
        MJPEGEncoder(),
        FileOutput(output),
        quality=quality,
    )


def stop_camera(cam):
    if cam.started:
        cam.stop_recording()


def get_current_enabled(cam):
    return cam.started


def get_current_size(cam):
    return getattr(cam, '_fpv_size', DEFAULT_CAMERA_SIZE)


def get_current_quality(cam):
    return QUALITY_TO_INT[getattr(cam, '_fpv_quality', DEFAULT_CAMERA_QUALITY)]


def process_request(app, req):
    cam = app['camera']
    output = app['output']

    stop_camera(cam)

    cam._fpv_size = (req['res_x'], req['res_y'])
    cam.configure(
        cam.create_video_configuration(
            main={'size': cam._fpv_size},
            transform=Transform(**CAMERA_TRANSFORM),
        )
    )
    cam._fpv_quality = INT_TO_QUALITY[req['quality']]

    if req['enabled']:
        start_camera(cam, output)
