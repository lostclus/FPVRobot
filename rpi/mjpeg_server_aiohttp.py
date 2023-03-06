import asyncio
import io
import threading
import time
import weakref

from aiohttp import web
from aiohttp import MultipartWriter
from libcamera import controls, Transform
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    return web.Response(
        text=PAGE,
        content_type='text/html',
    )


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


@routes.get('/stream.mjpg')
async def stream_mjpg(request):
    boundary = 'FRAME'
    resp = web.StreamResponse(
        headers={
            'Age': '0',
            'Cache-Control': 'no-cache, private',
            'Pragma': 'no-cache',
            'Content-Type': f'multipart/x-mixed-replace;boundary={boundary}',
        },
    )
    await resp.prepare(request)
    loop = asyncio.get_running_loop()
    output = request.app['output']
    request.app['streams'].add(resp)
    try:
        while True:
            frame = await loop.run_in_executor(None, output.get_frame)
            with MultipartWriter('image/jpeg', boundary=boundary) as mpwriter:
                mpwriter.append(frame, {
                    'Content-Type': 'image/jpeg'
                })
                await mpwriter.write(resp, close_boundary=False)
            await resp.drain()
        return resp
    finally:
        request.app['streams'].discard(resp)


app = web.Application()
app.add_routes(routes)

app['picam2'] = picam2 = Picamera2()
picam2.configure(
    picam2.create_video_configuration(
        main={'size': (640, 480)},
        transform=Transform(hflip=True, vflip=True),
    )
)
picam2.set_controls({'AwbEnable': True})
app['output'] = output = StreamingOutput()
picam2.start_recording(MJPEGEncoder(), FileOutput(output))
app['streams'] = weakref.WeakSet()

async def on_shutdown(app):
    for resp in set(app['streams']):
        resp.task.cancel()
    app['picam2'].stop_recording()

app.on_shutdown.append(on_shutdown)
web.run_app(app)
