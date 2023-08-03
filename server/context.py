from __future__ import annotations

import asyncio
from asyncio import Future
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from .utils import MISSING, RconClient

if TYPE_CHECKING:
    from . import BaseServer
    from .core.config import UserData

__all__ = ("Context",)


class Context:
    def __init__(
        self,
        server: "BaseServer",
        sid: str,
        user: "UserData",
        auth: dict = {},
    ) -> None:
        self.sid = sid
        self.server = server
        self.log = server.log
        self.user = user
        self.auth = auth
        self._extra_command_wait: dict[str, list[Future[dict]]] = {}
        self.server.add_listener(self._cmd_callback_callback, name="cmd_callback")

        self.rcon: RconClient | None = None

        # check rcon config is valid
        if isinstance(rcon := self.auth.get("rcon"), dict):
            self.rcon = RconClient(
                host=rcon.get("ip", None),
                port=rcon.get("port", None),
                password=rcon.get("password", None),
                loop=server.loop,
            )

    async def _cmd_callback_callback(self, ctx: "Context", result: dict) -> None:
        if not (command := result.get("command")):
            self.log.error("extra_command_callback: command is missing")
            return

        for wait in self._extra_command_wait.get(command, []):
            wait.set_result(result)

    async def extra_command(
        self,
        command: str,
        *,
        timeout: float | None = None,
    ) -> dict:
        """call MCDR client extra command"""
        await self.emit("extra_command", command)

        wait = Future[dict](loop=self.server.loop)
        self._extra_command_wait[command] = wait

        return await asyncio.wait_for(wait, timeout=timeout)

    async def emit(
        self,
        event: str,
        *data: Optional[Any],
        to: Optional[str] = MISSING,
        room: Optional[str] = None,
        skip_sid: Optional[Union[List[str], str]] = None,
        namespace: Optional[str] = None,
        callback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> None:
        """emit event to client"""
        await self.server.sio_server.emit(
            event=event,
            data=data,
            to=self.sid if to is MISSING and self.sid and not skip_sid else to,
            room=room,
            skip_sid=skip_sid if type(skip_sid) is list else [skip_sid],
            namespace=namespace,
            callback=callback,
            **kwargs,
        )

    async def disconnect(
        self,
        *,
        sid: str = MISSING,
        namespace: Optional[str] = None,
        ignore_queue: bool = False,
    ) -> None:
        """disconnect client"""
        await self.server.sio_server.disconnect(
            sid=self.sid if sid is MISSING else sid,
            namespace=namespace,
            ignore_queue=ignore_queue,
        )

    @property
    def display_name(self) -> str:
        """get user display name"""
        return self.user.display_name or self.user.name

    async def execute_command(self, command: str, exc_timeout: bool = True):
        """execute command on rcon"""
        if not self.rcon:
            return ...

        await self.rcon.connect()
        try:
            return await self.rcon.execute(command)
        except TimeoutError as e:
            if exc_timeout:
                raise e

    @property
    def name(self) -> str:
        return self.user.name

    def __del__(self) -> None:
        self.server.remove_listener(
            self._cmd_callback_callback,
            name="cmd_callback",
        )

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Context):
            return self.user.name == other.user.name and self.sid == other.sid
        if isinstance(other, str):
            return self.user.name == other

    def __str__(self) -> str:
        return self.display_name

    __repr__ = __str__
