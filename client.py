import asyncio
from chatbridgee.utils.client import event, BaseClient


class Test(BaseClient):
    def __init__(self):
        super().__init__("test")

    @event("connect")
    async def on_connect(self):
        await asyncio.sleep(1)
        print("connect")

    @event("message")
    async def on_message(self, sid: str, data: dict):
        print("message", sid, data)


client = Test()
client.start()

# @client.on("connect")
# def connect():
#     client.send("test")


# # asyncio.run(client.main)
# client.start()
# @event
# def test():
#     print("awa")


# @event("awa")
# def test2():
#     print("awa")


# test
# test2
