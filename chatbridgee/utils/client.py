import asyncio
import signal
from typing import (
    Dict,
    List,
    Callable,
    ClassVar,
    Iterable,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
)
import socketio

from chatbridgee.core.structure import PayloadSender, PayloadStructure
from chatbridgee.utils.events import Events, event

from .utils import CallableAsync

__all__ = ("BaseClient", "event")


R = TypeVar("R")
P = ParamSpec("P")


def _cancel_tasks(loop: asyncio.AbstractEventLoop) -> None:
    if not (tasks := {t for t in asyncio.all_tasks(loop=loop) if not t.done()}):
        return

    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "run shutdown.",
                    "exception": task.exception(),
                    "task": task,
                }
            )


class BaseClient(Events):
    events: ClassVar[Dict[str, List[Callable]]]

    def __init__(self, name: str, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.__name = name
        self._closed: bool = False

        self.sio = socketio.AsyncClient()
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._connected = asyncio.Event()

        super().__init__(self.loop)

    def handle_events(self) -> None:
        sio = self.sio

        @sio.on("*")
        async def call_listeners(ev_name: str, *args, **kwargs):
            self.dispatch(ev_name, *args, **kwargs)

        @sio.on("connect")
        async def on_connect(*args, **kwargs):
            self._connected.set()
            print("connect")
            await call_listeners("connect", *args, **kwargs)

        @sio.on("connect_error")
        async def on_connect_error(*args, **kwargs):
            await call_listeners("connect_error", *args, **kwargs)

        @sio.on("disconnect")
        async def on_disconnect(*args, **kwargs):
            await call_listeners("disconnect", *args, **kwargs)

    def get_name(self) -> str:
        return self.__name

    def _to_sync(self, func: Callable[P, R]):
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            return CallableAsync(func, loop=self.loop)(*args, **kwargs)

        return wrapper

    def send_to(
        self,
        type_: str,
        clients: Union[str, Iterable[str]],
        structure: PayloadSender,
    ) -> None:
        self.call(
            type_,
            PayloadStructure(
                data=structure,
                sender=self.get_name(),
                receivers=(clients,) if type(clients) == str else clients,
            ),
        )

    def send_to_all(self, type_: str, structure: PayloadSender) -> None:
        self.send_to(type_, [], structure)

    def wait_connect(self, callable_async: Callable[P, R]):
        async def wait_connect(*args: P.args, **kwargs: P.kwargs):
            await self._connected.wait()
            await callable_async(*args, **kwargs)

        return self._to_sync(wait_connect)

    # sio methods
    @property
    def emit(self):
        return self.wait_connect(self.sio.emit)

    @property
    def send(self):
        return self.wait_connect(self.sio.send)

    @property
    def call(self):
        return self.wait_connect(self.sio.call)

    @property
    def disconnect(self):
        return self.wait_connect(self.sio.disconnect)

    # end sio methods

    def is_closed(self) -> bool:
        return self._closed

    async def runner(self) -> None:
        self.handle_events()

        await self.sio.connect(
            "http://localhost:6000",
            {"username": "user", "password": "password_"},
        )
        await self.sio.wait()

    def start(self) -> None:
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            loop.add_signal_handler(signal.SIGTERM, loop.stop)
        except (NotImplementedError, RuntimeError):
            pass

        def stop_loop(_):
            loop.stop()

        future = asyncio.ensure_future(self.runner(), loop=loop)
        future.add_done_callback(stop_loop)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            future.remove_done_callback(stop_loop)

            _cancel_tasks(self.loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    def stop(self) -> None:
        if self._closed:
            return

        self._closed = True
        self.disconnect()
