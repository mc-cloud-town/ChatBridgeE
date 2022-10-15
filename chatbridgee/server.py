from aiohttp import web
import socketio

sio = socketio.AsyncServer()
app = web.Application()

sio.attach(app)


@sio.event
async def connect(sid: str, environ):
    # print(environ)
    ...
    # username = authenticate_user(environ)
    # with sio.session(sid) as session:
    #     session["username"] = username


@sio.event
async def message(sid, data):
    print("message from ", sid, data)


@sio.event
async def test(sid, data):
    print(sid, data)


# def authenticate_user():
#     ...

if __name__ == "__main__":
    web.run_app(app, port=6000)
