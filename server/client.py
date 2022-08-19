import asyncio
import socketio

sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("connection established")


@sio.event
async def disconnect():
    print("disconnected from server")


async def main():
    await sio.connect(
        "http://localhost:6000", {"username": "user", "password": "password_"}
    )
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(main())
