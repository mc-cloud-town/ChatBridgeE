import asyncio
from datetime import datetime
import time
from chatbridgee.utils.client import event, BaseClient


class Test(BaseClient):
    def __init__(self):
        super().__init__("test")

    @event("connect")
    async def on_connect(self):
        print("connect")
        while True:
            await asyncio.sleep(1)
            self.call("test", datetime.now().strftime("%H:%M:%S"))

    @event("message")
    async def on_message(self, sid: str, data: dict):
        print("message", sid, data)


client = Test()
client.call("awa", "awa")

time.sleep(2)
client.start()
