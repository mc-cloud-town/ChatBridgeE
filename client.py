import asyncio
import socketio

sio = socketio.AsyncClient()


@sio.event
async def connect():
    print("connection established")

    for d in [
        # server_start
        ["server_start", []],
        # server_stop
        ["server_stop", []],
        # player_chat
        ["player_chat", ["monkey", "hello"]],
        ["player_chat", ["monkey", "10"]],
        # player_joined
        ["player_joined", ["monkey"]],
        # player_left
        ["player_left", ["monkey"]],
    ]:
        await sio.emit(*d)

    # server_start(server_name: str)
    # server_stop(server_name: str)
    # player_chat(server_name: str, player_name: str, content: str)
    # player_joined(server_name: str, player_name: str)
    # player_left(server_name: str, player_name: str)


@sio.event
async def disconnect():
    print("disconnected from server")


async def main():
    await sio.connect("http://localhost:8080", auth={"name": "test", "password": "awa"})
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(main())
