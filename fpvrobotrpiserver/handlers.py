import asyncio
from pathlib import Path

from aiohttp import web
from aiohttp import MultipartWriter

from .motor_servo import new_message, write_message

routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    with open(Path(__file__).parent / 'index.html') as fp:
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
    request.app['streams'].add(resp)
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
        request.app['streams'].discard(resp)


@routes.post('/motor-servo')
async def motor_servo(request):
    ser = request.app['motor_servo_serial']
    data = await request.json()
    msg = new_message(device=data['device'], value=data['value'])
    await write_message(ser, msg)
    return web.json_response({"ok": True})
