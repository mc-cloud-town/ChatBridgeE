from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from server.utils import RconClient

from .utils import MISSING

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

        self.rcon: RconClient | None = None

        if isinstance(rcon := self.auth.get("rcon"), dict):
            self.rcon = RconClient(
                host=rcon.get("ip", None),
                port=rcon.get("port", None),
                password=rcon.get("password", None),
                loop=server.loop,
            )

    def __str__(self) -> str:
        return self.display_name

    __repr__ = __str__

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
        await self.server.sio_server.disconnect(
            sid=self.sid if sid is MISSING else sid,
            namespace=namespace,
            ignore_queue=ignore_queue,
        )

    @property
    def display_name(self) -> str:
        return self.user.display_name or self.user.name

    async def setup_rcon(self) -> None:
        if not (rcon := self.rcon):
            raise Exception("client no give rcon auth data")

        if rcon.is_connected:
            return

        await rcon.connect()

    async def execute_command(self, command: str, exc_timeout: bool = True):
        if not self.rcon:
            return ...

        await self.rcon.connect()
        try:
            return await self.rcon.execute(command)
        except TimeoutError as e:
            if exc_timeout:
                raise e
