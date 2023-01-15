from typing import TYPE_CHECKING, Any, Callable, Optional, List

from .utils import MISSING

if TYPE_CHECKING:
    from .server import Server


class Context:
    def __init__(self, server: "Server", sid: str) -> None:
        self.sid = sid
        self.server = server

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
