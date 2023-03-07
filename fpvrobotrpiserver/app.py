import weakref
from contextlib import contextmanager

import aioserial
from aiohttp import web

from .handlers import routes
from .camera import create_camera, stop_camera


async def on_shutdown(app):
    for resp in set(app['streams']):
        resp.task.cancel()
    for ws in set(app['websockets']):
        await ws.close()


@contextmanager
def create_app():
    app = web.Application()
    app.add_routes(routes)

    app['camera'], app['output'] = create_camera()
    app['streams'] = weakref.WeakSet()
    app['websockets'] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)

    with aioserial.AioSerial('/dev/serial0', 9600, timeout=3) as ser:
        app['motor_servo_serial'] = ser
        yield app

    stop_camera(app['camera'])
    del app['camera']
    del app['output']
