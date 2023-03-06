import weakref

from aiohttp import web

from .handlers import routes
from .camera import create_camera, stop_camera


async def on_shutdown(app):
    for resp in set(app['streams']):
        resp.task.cancel()
    stop_camera(app['camera'])


def create_app():
    app = web.Application()
    app.add_routes(routes)
    app['camera'], app['output'] = create_camera()
    app['streams'] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)
    return app
