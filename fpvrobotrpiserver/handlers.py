import asyncio
import json
from pathlib import Path

from aiohttp import MultipartWriter, WSMsgType, web

from . import ard0, camera

ROOT_PATH = Path(__file__).parent

routes = web.RouteTableDef()
routes.static('/static', ROOT_PATH / 'static')


@routes.get('/')
async def index(request):
    with open(ROOT_PATH / 'index.html') as fp:
        text = fp.read()
    return web.Response(
        text=text,
        content_type='text/html',
    )


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
async def ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app['websockets'].add(ws)
    try:
        async for msg in ws:
            if msg.type == WSMsgType.PING:
                await ws.pong()
            elif msg.type == WSMsgType.TEXT:
                req_data = json.loads(msg.data)
                req_type = req_data.pop('type')
                if req_type == 'ard0':
                    ser = request.app['ard0_serial']
                    req = ard0.new_requset(**req_data)
                    await ard0.write_request(ser, req)
                if req_type == 'cam':
                    cam = request.app['camera']
                    camera.process_request(request.app, req_data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
        return ws
    finally:
        request.app['websockets'].discard(ws)
