from typing import Dict
from aiohttp import web
import socketio

sio_server = socketio.AsyncServer()
app = web.Application()

sio_server.attach(app)


@sio_server.event
async def connect(sio: str, environ: Dict):
    # print(environ)
    await sio_server.emit("test", {"test": "test"})
    ...
    # username = authenticate_user(environ)
    # with sio.session(sid) as session:
    #     session["username"] = username


@sio_server.event
async def message(sid, data):
    print("message from ", sid, data)


@sio_server.on("*")
async def test(sid, data):
    print(sid, data)


def start():
    web.run_app(app, port=6000)


if __name__ == "__main__":
    start()
