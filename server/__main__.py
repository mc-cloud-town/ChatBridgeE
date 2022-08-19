from aiohttp import web
import socketio

sio = socketio.AsyncServer()
app = web.Application()

sio.attach(app)


@sio.event
async def connect(sid: str, environ):
    print(environ)
    # username = authenticate_user(environ)
    # with sio.session(sid) as session:
    #     session["username"] = username


# @sio.event
# async def message(sid, data):
#     with sio.session(sid) as session:
#         print("message from ", session["username"])


# def authenticate_user():
#     ...

if __name__ == "__main__":
    web.run_app(app, port=6000)
