from datetime import datetime
from typing import Dict
from aiohttp import web
import socketio

sio_server = socketio.AsyncServer()
app = web.Application()

sio_server.attach(app)


@sio_server.event
async def connect(sio: str, environ: Dict):
    print(sio)
    ...
    # username = authenticate_user(environ)
    # with sio.session(sid) as session:
    #     session["username"] = username


@sio_server.event
async def disconnect(*args):
    print("disconnect", args)


@sio_server.on("*")
async def test(*args):
    print(datetime.now().strftime("%H:%M:%S"), args)


def start():
    web.run_app(app, port=6000)


if __name__ == "__main__":
    start()
