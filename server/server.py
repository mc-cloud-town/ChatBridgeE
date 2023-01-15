import asyncio
import inspect
import sys
import traceback
from typing import Any, Callable, Coroutine, TypeVar
from socketio import AsyncServer

from aiohttp import web

from .context import Context
from .plugin import PluginMixin
from .utils import MISSING

CoroFunc = Callable[..., Coroutine[Any, Any, Any]]
CoroFuncT = TypeVar("CoroFuncT", bound=CoroFunc)


class BaseServer(PluginMixin):
    def __init__(self):
        super().__init__()

        self.extra_events: dict[str, list[CoroFunc]] = {}

        self.clients: dict[str, Context] = {}
        self.sio_server = AsyncServer()
        self.app = web.Application()

        self.sio_server.attach(self.app)
        self.__handle_events()

        self.app.on_shutdown.append(self.__on_shutdown)

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

    def listen(self, name: str = MISSING) -> Callable[[CoroFuncT], CoroFuncT]:
        def decorator(func: CoroFuncT) -> CoroFuncT:
            self.add_listener(func, name)
            return func

        return decorator

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        method = f"on_{event_name}"

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

        if method in self.extra_events:
            for func in self.extra_events.get(method, []):
                self._schedule_event(func, event_name, *args, **kwargs)

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            if asyncio.iscoroutinefunction(coro):
                # inhibition `TypeError takes x positional argument but x were given`
                if (count := self.__get_args_len(coro)) < len(args) and count != -1:
                    args = args[:count]
                await coro(*args, **kwargs)
            else:
                coro(*args, **kwargs)
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def __get_args_len(self, coro: Callable[..., Any]) -> int:
        count = 0
        for parameter in inspect.signature(coro).parameters.values():
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                return -1
            # TODO check else Parameter.kind
            if parameter.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                count += 1
        return count

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ):
        return asyncio.create_task(
            self._run_event(coro, event_name, *args, **kwargs),
            name=f"ChatBridgeE: {event_name}",
        )

    # ----- `on_` events -----

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        print(f"Ignoring exception in {event_method}", file=sys.stderr)
        traceback.print_exc()

    async def on_connect(self, ctx: Context, auth):
        pass

    async def on_message(self, ctx: Context, msg: Any):
        pass

    async def on_disconnect(self, ctx: Context):
        pass

    def __handle_events(self) -> None:
        sio_server = self.sio_server

        @sio_server.event
        async def connect(sid, _, auto) -> None:
            self.clients[sid] = (ctx := self.get_context(sid))

            self.dispatch("connect", ctx, auto)

        @sio_server.event
        async def disconnect(sid: str) -> None:
            self.dispatch("disconnect", self.clients.pop(sid, self.get_context(sid)))

        @sio_server.on("*")
        async def else_events(event_name: str, sid: str, *args: Any) -> None:
            self.dispatch(event_name, self.get_context(sid), *args)

    def get_context(self, sid: str):
        ctx = Context(self, sid)

        return ctx

    def parse_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        ...

    def start(self):
        web.run_app(self.app)

    async def __on_shutdown(self, app: web.Application):
        # use copy inhibition `RuntimeError: dictionary changed size during iteration`
        for client in self.clients.copy().values():
            # TODO sleep all stop
            await client.disconnect()
