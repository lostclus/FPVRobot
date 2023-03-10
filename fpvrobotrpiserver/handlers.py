import asyncio
import json
from pathlib import Path

from aiohttp import MultipartWriter, WSMsgType, web

from .motor_servo import new_requset, write_request

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


@routes.post('/motor-servo')
async def motor_servo(request):
    ser = request.app['motor_servo_serial']
    data = await request.json()
    msg = new_message(device=data['device'], value=data['value'])
    await write_message(ser, msg)
    return web.json_response({"ok": True})


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
                data = json.loads(msg.data)
                ser = request.app['motor_servo_serial']
                await write_request(ser, new_requset(**data))
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
        return ws
    finally:
        request.app['websockets'].discard(ws)
