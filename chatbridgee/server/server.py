from typing import Any, Dict, Optional

from aiohttp import web
import socketio

from chatbridgee.utils.events import Events
from chatbridgee.utils.plugin import Plugin


class Server(Events):
    def __init__(self) -> None:
        self.app = web.Application()
        self.sio_server = socketio.AsyncServer()
        self.sio_server.attach(self.app)

        self.plugins: Dict[str, Plugin] = {}

        self.handle_events()

    def handle_events(self) -> None:
        sio_server = self.sio_server

        @sio_server.event
        async def connect(*args: Any) -> None:
            self.dispatch("disconnect", *args)

        @sio_server.event
        async def disconnect(*args: Any) -> None:
            self.dispatch("disconnect", *args)

        @sio_server.on("*")
        async def else_events(event_name: str, *args: Any) -> None:
            self.dispatch(event_name, *args)

    def add_plugin(self, plugin: Plugin) -> None:
        # TODO add callbacks
        self.add_plugin(plugin)

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self.plugins.get(name)

    def remove_plugin(self, name: str) -> Optional[Plugin]:
        plugin = self.plugins.pop(name, None)

        # TODO remove callbacks

        return plugin

    def run(self, port: Optional[int] = 6000, **kwargs: Any) -> None:
        web.run_app(self.app, port=port, **kwargs)
