from typing import Any, Callable, Generic, Optional, TypeVar, ParamSpec, Union

import asyncio

__all__ = ("MISSING", "CallableAsync", "to_sync")


class _MissingSentinel:
    def __eq__(self, _) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


R = TypeVar("R")
P = ParamSpec("P")


class CallableAsync(Generic[R, P]):
    _func: Callable[P, R]

    def __init__(
        self,
        func: Union[Callable[P, R], "CallableAsync"],
        loop: Optional[asyncio.AbstractEventLoop],
    ) -> None:
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._func = func._func if isinstance(func, CallableAsync) else func

    def __call__(self, *args: P.args, **kwargs: P.kwargs):
        return self.sync(*args, **kwargs)

    async def asynchronous(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return await self._run(*args, **kwargs)

    def sync(self, *args: P.args, **kwargs: P.kwargs):
        return self.loop.create_task(
            self._run(*args, **kwargs),
            name=f"chatbridge: {self._func.__name__}",
        )

    async def _run(self, *args: P.args, **kwargs: P.kwargs) -> R:
        if not asyncio.iscoroutinefunction(self._func):
            return self._func(*args, **kwargs)
        return await self._func(*args, **kwargs)


def to_sync(func: Callable = MISSING):
    if isinstance(func, CallableAsync):
        raise TypeError("Callback is already a CallableAsync.")

    if func is MISSING:
        return to_sync

    return CallableAsync(func)
