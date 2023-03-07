from aiohttp import web

from .app import create_app


with create_app() as app:
    web.run_app(app)
