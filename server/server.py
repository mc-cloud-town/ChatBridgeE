import asyncio
import sys
import traceback
from typing import Any, Callable, Coroutine, TypeVar
from socketio import AsyncServer

from server.plugin import PluginMixin
from server.utils import MISSING

CoroFunc = Callable[..., Coroutine[Any, Any, Any]]
CoroFuncT = TypeVar("CoroFuncT", bound=CoroFunc)


class Server(AsyncServer, PluginMixin):
    def __init__(self):
        super().__init__()

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

        if event_name in self.extra_events:
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
            await coro(event_name, *args, **kwargs)
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

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
