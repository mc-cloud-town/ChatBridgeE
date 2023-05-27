import asyncio
import inspect
import logging
import os
from asyncio import AbstractEventLoop
from typing import Any, Callable, Coroutine, List, Optional, TypeVar, Union

from aiohttp import web
from socketio import AsyncServer

from ..context import Context
from ..plugin import PluginMixin
from ..utils import MISSING, FormatMessage
from . import CommandManager
from .config import Config, UserData

__all__ = ("BaseServer",)

log = logging.getLogger("chat-bridgee")

CoroFunc = Callable[..., Coroutine[Any, Any, Any]]
CoroFuncT = TypeVar("CoroFuncT", bound=CoroFunc)


class BaseServer(PluginMixin):
    def __init__(
        self,
        config_type: str = "yaml",
        loop: AbstractEventLoop | None = None,
    ):
        super().__init__()

        self.loop = asyncio.get_running_loop() if loop is None else loop
        self.extra_events: dict[str, list[CoroFunc]] = {}

        self.clients: dict[str, Context] = {}
        self.sio_server = AsyncServer()
        self.app = web.Application(loop=self.loop)
        self.command_manager = CommandManager(self)
        self.log = log
        self.config = Config("chatbridgee-config", config_type=config_type)

        self.sio_server.attach(self.app)
        self.__handle_events()

        self.app.on_shutdown.append(self.__on_shutdown)

    def add_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Listeners must be coroutines")

        if not name.startswith("on_"):
            name = f"on_{name}"
        if name.startswith("on_command_"):
            self.command_manager.add_command(" ".join(name.split("_")[2:]))

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name

        # remove command
        if name.startswith("on_command_"):
            self.command_manager.remove_command(" ".join(name.split("_")[2:]))

        # remove event
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
        log.debug(f"Dispatching event {event_name!r}, {args}, {kwargs}")

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

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
        log.exception(f"Ignoring exception in {event_method}")

    async def on_connect(self, ctx: Context, auth):
        pass

    async def on_message(self, ctx: Context, msg: Any):
        pass

    async def on_disconnect(self, ctx: Context):
        pass

    async def on_cmd_callback(self, ctx: Context, result: str):
        pass

    def __handle_events(self) -> None:
        sio_server = self.sio_server

        @sio_server.event
        async def connect(sid: str, _, auth: Any) -> None:
            try:
                if not (user := self.check_user(auth["name"], auth["password"])):
                    log.info(f"客戶端登入失敗 {auth['name']}")
                    raise PermissionError
            except (TypeError, KeyError, PermissionError):
                log.info(f"客戶端登入失敗 {sid}")
                await self.sio_server.emit("error", "登入失敗", room=sid)
                await self.sio_server.disconnect(sid)
                return
            self.log.debug(f"客戶端登入成功 {user.name}")
            self.clients[sid] = (ctx := self.create_context(sid, user, auth))
            self.dispatch("connect", ctx, auth)

        @sio_server.event
        async def disconnect(sid: str) -> None:
            if (client := self.clients.pop(sid, None)) is None:
                del client  # run delete func，remove client event handler
                return

            self.dispatch("disconnect", client)

        @sio_server.on("*")
        async def else_event(event_name: str, sid: str, data: Any = None) -> None:
            log.debug(f"收到從 {sid} 發送的事件 {event_name}")
            args = [data]

            if type(data) is list:
                args = data

            self.dispatch(event_name, self.clients.get(sid), *args)

    def create_context(self, sid: str, user: UserData, auth: dict = {}) -> Context:
        return Context(self, sid, user, auth)

    async def start(self) -> web.AppRunner:
        runner = web.AppRunner(self.app)
        await runner.setup()
        port = int(self.config.get("port", os.getenv("PORT")))
        site = web.TCPSite(runner, "localhost", port)
        await site.start()

        print(f"======= Serving on http://localhost:{port}/ ======")

        return runner

    async def __on_shutdown(self, app: web.Application):
        # use copy inhibition `RuntimeError: dictionary changed size during iteration`
        for client in self.clients.copy().values():
            await client.disconnect()

    def check_user(self, name: str, password: str) -> Optional[UserData]:
        users = self.config.get("users", {})
        try:
            if (user := users.get(name)) and user.get("password") == password:
                return UserData(
                    name=name,
                    display_name=user.get("display_name"),
                )
        except TypeError:
            pass

        return None

    def get_client(self, name: str) -> Optional[Context]:
        for client in self.clients.values():
            if client.user.name == name:
                return client

        return None

    async def emit(
        self,
        event: str,
        *data: Optional[Any],
        to: Optional[str] = None,
        room: Optional[str] = None,
        skip_sid: Optional[Union[List[str], str]] = None,
        namespace: Optional[str] = None,
        callback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> None:
        await self.sio_server.emit(
            event=event,
            data=data,
            to=to,
            room=room,
            skip_sid=skip_sid if type(skip_sid) is list else [skip_sid],
            namespace=namespace,
            callback=callback,
            **kwargs,
        )

    async def send(
        self,
        msg: Union[str, FormatMessage, Any],
        server_name: str = None,
        to: Optional[str] = None,
        room: Optional[str] = None,
        skip_sid: Optional[Union[List[str], str]] = None,
        namespace: Optional[str] = None,
        callback: Optional[Callable[..., Any]] = None,
        format: Optional[bool] = True,
        no_mark: bool = False,
        **kwargs: Any,
    ):
        if isinstance(msg, str) and format:
            msg = FormatMessage(msg, no_mark=no_mark)
        elif isinstance(msg, (list, tuple)):
            msg = FormatMessage(*msg, no_mark=no_mark)

        if server_name:
            msg = FormatMessage(f" {server_name}: ", msg)

        if isinstance(msg, FormatMessage):
            msg = msg.__dict__

        await self.sio_server.emit(
            event="chat",
            data=msg,
            to=to,
            room=room,
            skip_sid=skip_sid if type(skip_sid) is list else [skip_sid],
            namespace=namespace,
            callback=callback,
            **kwargs,
        )
