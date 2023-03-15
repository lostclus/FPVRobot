import io
import threading

from libcamera import controls, Transform
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput

from .config import CAMERA_SIZE, CAMERA_TRANSFORM


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
            main={'size': CAMERA_SIZE},
            transform=Transform(**CAMERA_TRANSFORM),
        )
    )
    cam.set_controls({'AwbEnable': True})
    output = StreamingOutput()
    return (cam, output)


def start_camera(cam, output, quality=Quality.MEDIUM):
    cam.start_recording(
        MJPEGEncoder(),
        FileOutput(output),
        quality=quality,
    )


def stop_camera(cam):
    cam.stop_recording()


def process_request(app, req):
    cam = app['camera']
    output = app['output']

    stop_camera(cam)

    cam.configure(
        cam.create_video_configuration(
            main={'size': (req['res_x'], req['res_y'])},
            transform=Transform(**CAMERA_TRANSFORM),
        )
    )

    quality = {
        0: Quality.VERY_LOW,
        1: Quality.LOW,
        2: Quality.MEDIUM,
        3: Quality.HIGH,
        4: Quality.VERY_HIGH,
    }[req['quality']]

    start_camera(cam, output, quality=quality)
