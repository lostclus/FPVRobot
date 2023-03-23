import asyncio
import json
import subprocess
from pathlib import Path

import aiohttp_jinja2
from aiohttp import MultipartWriter, WSMsgType, web

from . import ard1, camera

ROOT_PATH = Path(__file__).parent

routes = web.RouteTableDef()
routes.static('/static', ROOT_PATH / 'static')


@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def index_handler(request):
    cam = request.app['camera']
    res_x, res_y = camera.get_current_size(cam)
    return {
        'camera_enabled': int(camera.get_current_enabled(cam)),
        'resolution': f'{res_x}x{res_y}',
        'quality': camera.get_current_quality(cam),
    }


@routes.get('/stream.mjpg')
async def video_stream_handler(request):
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
    request.app['tasks'].add(resp.task)
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
        request.app['tasks'].discard(resp.task)


@routes.get('/ws')
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app['websockets'].add(ws)
    try:
        async for msg in ws:
            if msg.type == WSMsgType.PING:
                await ws.pong()
            elif msg.type == WSMsgType.TEXT:
                req_data = json.loads(msg.data)
                ser = request.app['ard1_serial']
                req = ard1.new_requset(**req_data)
                await ard1.write_request(ser, req)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
        return ws
    finally:
        request.app['websockets'].discard(ws)


@routes.post('/camera')
async def camera_handler(request):
    req_data = await request.json()
    camera.process_request(request.app, req_data)
    return web.json_response({})


@routes.post('/power-off')
async def power_off_handler(request):
    subprocess.run(["sudo", "poweroff"])
    return web.json_response({})
