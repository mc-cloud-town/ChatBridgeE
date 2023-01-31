import asyncio
import inspect
import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar, Union, List

from aiohttp import web
from socketio import AsyncServer

from ..context import Context
from ..plugin import PluginMixin
from ..utils import MISSING
from . import CommandManager, Config
from .config import UserAuth

__all__ = ("BaseServer",)

log = logging.getLogger("chat-bridgee")

CoroFunc = Callable[..., Coroutine[Any, Any, Any]]
CoroFuncT = TypeVar("CoroFuncT", bound=CoroFunc)


class BaseServer(PluginMixin):
    def __init__(self, config_type: str = "yaml"):
        super().__init__()

        self.extra_events: dict[str, list[CoroFunc]] = {}

        self.clients: dict[str, Context] = {}
        self.sio_server = AsyncServer()
        self.app = web.Application()
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
        log.exception(f"Ignoring exception in {event_method}")

    async def on_connect(self, ctx: Context, auth):
        pass

    async def on_message(self, ctx: Context, msg: Any):
        pass

    async def on_disconnect(self, ctx: Context):
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
            self.log.info(f"客戶端登入成功 {user['name']}")
            self.clients[sid] = (ctx := self.get_context(sid, user))
            self.dispatch("connect", ctx, auth)

        @sio_server.event
        async def disconnect(sid: str) -> None:
            if (client := self.clients.pop(sid, None)) is None:
                return

            self.dispatch("disconnect", client)

        @sio_server.on("*")
        async def else_event(event_name: str, sid: str, data: Any = None) -> None:
            log.debug(f"收到從 {sid} 發送的事件 {event_name}")
            args = [data]

            if type(data) is list:
                args = data

            self.dispatch(event_name, self.clients.get(sid), *args)

    def get_context(self, sid: str, user: UserAuth) -> Context:
        return Context(self, sid, user)

    async def start(self) -> web.AppRunner:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8080)
        await site.start()

        print("======= Serving on http://127.0.0.1:8080/ ======")

        return runner

    async def __on_shutdown(self, app: web.Application):
        # use copy inhibition `RuntimeError: dictionary changed size during iteration`
        for client in self.clients.copy().values():
            # TODO sleep all stop
            await client.disconnect()

    def check_user(self, name: str, password: str) -> Optional[UserAuth]:
        users = self.config.get("users", {})

        try:
            if (user := dict(users.get(name))) is not None and user.get(
                "password"
            ) == password:
                return UserAuth(
                    name=name,
                    password=password,
                    display_name=user.get("display_name"),
                )
        except TypeError:
            pass

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
