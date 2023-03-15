import asyncio
import weakref
from contextlib import contextmanager

from aiohttp import web

from . import ard0, camera
from .handlers import routes


async def on_startup(app):
    ser = app['ard0_serial']
    task = asyncio.create_task(ard0.process_responses(ser, app))
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

    app['camera'], app['output'] = camera.create_camera()
    app['tasks'] = weakref.WeakSet()
    app['websockets'] = weakref.WeakSet()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    camera.start_camera(app['camera'], app['output'])
    try:
        with ard0.create_serial() as ser:
            app['ard0_serial'] = ser
            yield app
    finally:
        camera.stop_camera(app['camera'])
        del app['camera']
        del app['output']
