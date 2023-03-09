import asyncio
import weakref
from contextlib import contextmanager

from aiohttp import web

from .handlers import routes
from .camera import create_camera, stop_camera
from .motor_servo import create_serial, process_messages


async def on_startup(app):
    ser = app['motor_servo_serial']
    task = asyncio.create_task(process_messages(ser, app))
    app['tasks'].add(task)


async def on_shutdown(app):
    for task in set(app['tasks']):
        task.cancel()
    for ws in set(app['websockets']):
        await ws.close()


@contextmanager
def create_app():
    app = web.Application()
    app.add_routes(routes)

    app['camera'], app['output'] = create_camera()
    app['tasks'] = weakref.WeakSet()
    app['websockets'] = weakref.WeakSet()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    with create_serial() as ser:
        app['motor_servo_serial'] = ser
        yield app

    stop_camera(app['camera'])
    del app['camera']
    del app['output']
