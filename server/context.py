from typing import TYPE_CHECKING, Any, Callable, List, Optional

from .utils import MISSING

if TYPE_CHECKING:
    from . import BaseServer
    from .core.config import UserAuth

__all__ = ("Context",)


class Context:
    def __init__(self, server: "BaseServer", sid: str, user: "UserAuth") -> None:
        self.sid = sid
        self.server = server
        self.log = server.log
        self.user = user

    async def emit(
        self,
        event: str,
        data: Optional[Any] = None,
        *,
        to: Optional[str] = MISSING,
        room: Optional[str] = None,
        skip_sid: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        callback: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> None:
        await self.server.sio_server.emit(
            event=event,
            data=data,
            to=self.sid if to is MISSING and self.sid else to,
            room=room,
            skip_sid=skip_sid,
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
