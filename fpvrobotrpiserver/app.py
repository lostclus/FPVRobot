import asyncio
import weakref
from contextlib import contextmanager
from pathlib import Path

import aiohttp_jinja2
import jinja2
from aiohttp import web

from . import ard1, camera
from .config import AUTH_USER, AUTH_PASSWORD
from .handlers import routes

ROOT_PATH = Path(__file__).parent


async def on_startup(app):
    ser = app['ard1_serial']
    task = asyncio.create_task(ard1.process_responses(ser, app))
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

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(ROOT_PATH),
    )

    if AUTH_USER and AUTH_PASSWORD:
        from aiohttp_basicauth import BasicAuthMiddleware
        app.middlewares.append(
            BasicAuthMiddleware(username=AUTH_USER, password=AUTH_PASSWORD)
        )

    app['camera'], app['output'] = camera.create_camera()
    app['tasks'] = weakref.WeakSet()
    app['websockets'] = weakref.WeakSet()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    camera.start_camera(app['camera'], app['output'])
    try:
        with ard1.create_serial() as ser:
            app['ard1_serial'] = ser
            yield app
    finally:
        camera.stop_camera(app['camera'])
        del app['camera']
        del app['output']
