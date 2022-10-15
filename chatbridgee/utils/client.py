import asyncio
import signal
from typing import Callable, Iterable, ParamSpec, TypeVar, Union
import socketio

from chatbridgee.core.structure import PayloadSender, PayloadStructure

from .utils import CallableAsync

__all__ = ("BaseClient",)


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


class BaseClient:
    sio = socketio.AsyncClient()

    def __init__(self, name: str):
        self.__name = name

        self.loop = asyncio.get_event_loop()

        @self.sio.event
        async def connect():
            print("connection established")

        @self.sio.event
        async def disconnect():
            print("disconnected from server")

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

    # sio methods
    @property
    def emit(self):
        return self._to_sync(self.sio.emit)

    @property
    def send(self):
        return self._to_sync(self.sio.send)

    @property
    def call(self):
        return self._to_sync(self.sio.call)

    @property
    def disconnect(self):
        return self._to_sync(self.sio.disconnect)

    @property
    def on(self):
        return self.sio.on

    # end sio methods

    async def runner(self) -> None:
        await self.sio.connect(
            "http://localhost:6000",
            {"username": "user", "password": "password_"},
        )
        await self.sio.wait()

    def start(self):
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
