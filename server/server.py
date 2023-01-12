import asyncio
from typing import Any, Callable, Coroutine
from socketio import AsyncServer

from server.plugin import PluginMixin
from server.utils import MISSING

CoroFunc = Callable[..., Coroutine[Any, Any, Any]]


class Server(AsyncServer, PluginMixin):
    def __init__(self):
        self.extra_events: dict[str, list[CoroFunc]] = {}

    def add_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Listeners must be coroutines")

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass
