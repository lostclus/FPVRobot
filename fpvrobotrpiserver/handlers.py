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
    async def send_session_state(ws):
        # Send to client session state message.
        await ws.send_json(
            {
                'type': 'session',
                'is_active': ws._fpv_is_active,
            }
        )

    app = request.app
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Determine if this session will be an active session. This session will be
    # active if no other active session exists.
    ws._fpv_is_active = not any(
        [other_ws._fpv_is_active for other_ws in app['websockets']]
    )
    await send_session_state(ws)
    # Add this web socket to global list of all web sockets.
    app['websockets'].add(ws)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.PING:
                await ws.pong()
            elif msg.type == WSMsgType.TEXT:
                req_data = json.loads(msg.data)
                req_type = req_data.pop('type')

                if req_type == 'ard1':
                    # ARD1 control message is received. Only active session
                    # accept control messages.
                    if not ws._fpv_is_active:
                        continue

                    # Forward message to ARD1 serial port.
                    ser = app['ard1_serial']
                    req = ard1.new_requset(**req_data)
                    await ard1.write_request(ser, req)

                elif req_type == 'session':
                    # Session state message is received
                    if req_data['is_active'] == ws._fpv_is_active:
                        continue

                    if req_data['is_active']:
                        # Set this session active. Set all other sessions not
                        # active.
                        for other_ws in app['websockets']:
                            other_ws._fpv_is_active = other_ws is ws
                            await send_session_state(other_ws)
                    else:
                        # Set this session not active
                        ws._fpv_is_active = False
                        await send_session_state(ws)

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())
        return ws
    finally:
        # Web socket is closed. Remove this web socket from list.
        app['websockets'].discard(ws)


@routes.post('/camera')
async def camera_handler(request):
    req_data = await request.json()
    camera.process_request(request.app, req_data)
    return web.json_response({})


@routes.post('/power-off')
async def power_off_handler(request):
    subprocess.run(["sudo", "poweroff"])
    return web.json_response({})
