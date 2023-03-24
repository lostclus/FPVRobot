from aiohttp import web

from .app import create_app
from .config import HOST, PORT


with create_app() as app:
    web.run_app(app, host=HOST, port=PORT)
