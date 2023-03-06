import io
import threading

from libcamera import controls, Transform
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput


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
    camera = Picamera2()
    camera.configure(
        camera.create_video_configuration(
            main={'size': (640, 480)},
            transform=Transform(hflip=True, vflip=True),
        )
    )
    camera.set_controls({'AwbEnable': True})
    output = StreamingOutput()
    camera.start_recording(MJPEGEncoder(), FileOutput(output))
    return (camera, output)


def stop_camera(camera):
    camera.stop_recording()
