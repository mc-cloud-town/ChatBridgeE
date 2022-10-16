import json
from typing import Any, Callable, Generic, Optional, TypeVar, ParamSpec

import asyncio

__all__ = ("MISSING", "ClassJson", "CallableAsync", "to_sync")


class _MissingSentinel:
    def __eq__(self, _) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


class ClassJson:
    def __init__(self, **kwargs) -> None:
        self.__kwargs = kwargs

    def __repr__(self) -> str:
        return json.dumps(self.__kwargs)

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key: str):
        return self.__kwargs.get(key, None)


R = TypeVar("R")
P = ParamSpec("P")


class CallableAsync(Generic[R, P]):
    _func: Callable[P, R]

    def __init__(
        self,
        func: Callable[P, R],
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self._func = func

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
        if asyncio.iscoroutinefunction(self._func):
            return await self._func(*args, **kwargs)
        return self._func(*args, **kwargs)


def to_sync(func: Optional[Callable] = None):
    if isinstance(func, CallableAsync):
        raise TypeError("Callback is already a CallableAsync.")

    if func is None:
        return to_sync

    return CallableAsync(func)
