import logging
import sys
from chatbridgee.core.client import BaseClient, event
from chatbridgee.core.structure import ChatEventStructure

log = logging.getLogger("chatbridgee")
log.setLevel(logging.DEBUG)

(ch := logging.StreamHandler(sys.stdout)).setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
log.addHandler(ch)


class Test(BaseClient):
    events_structure = {"test": ChatEventStructure}

    def __init__(self):
        super().__init__("test")

    @event("connect")
    def on_connect(self):
        print("connect")
        self.call("test", ChatEventStructure(time="awa", player="awa", content="awa"))

    @event("message")
    def on_message(self, sid: str, data: dict):
        print("message", sid, data)


client = Test()

client.start()
client.wait()
