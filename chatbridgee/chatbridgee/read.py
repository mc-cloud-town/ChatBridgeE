import socketio
from mcdreforged.api.all import PluginServerInterface


class ReadClient:
    def __init__(self, server: PluginServerInterface, sio: socketio.Client) -> None:
        self.server = server
        self.sio = sio

        self.sio.on("chat", self.on_chat)

    def on_chat(self, data: dict):
        ...
