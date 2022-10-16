import asyncio
from typing import (
    Any,
    Dict,
    List,
    Union,
    Callable,
    ClassVar,
    Generic,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    overload,
)

from chatbridgee.utils.utils import MISSING, CallableAsync


R = TypeVar("R")
P = ParamSpec("P")


class EventHandler(Generic[P, R]):
    def __init__(self, func: Callable[P, R], event_name: Optional[str] = None):
        self.__func = func
        self.event_name = func.__name__ if event_name is None else event_name

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.__func(*args, **kwargs)


# fmt: off
@overload  # noqa: E302
def event(arg: str) -> Callable[[Callable[P, R]], EventHandler[P, R]]: ...  # noqa: E704
@overload  # noqa: E302
def event(arg: Callable[P, R]) -> EventHandler[P, R]: ...  # noqa: E704
# fmt: on


def event(arg: Union[str, Callable[P, R]] = MISSING):
    if type(arg) == str:

        def decorator(func: Callable[P, R]):
            func.__name__ = arg
            return event(func)

        return decorator

    return EventHandler(arg, arg.__name__)


class EventsMate(type):
    extra_events: Dict[str, List[Callable]] = {}

    def __new__(cls: Type["EventsMate"], *args: Any, **kwargs: Any) -> "EventsMate":
        name, bases, attrs = args

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        events: Dict[str, List[Callable]] = {}

        for base in reversed(new_cls.__mro__):
            for _, func in base.__dict__.items():
                if not isinstance(func, EventHandler):
                    continue

                name = func.event_name
                events[name] = events.get(name, [])
                events[name].append(func)

        new_cls.extra_events = events

        return new_cls


class Events(metaclass=EventsMate):
    extra_events: ClassVar[Dict[str, List[Callable]]]

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.loop = loop

    def dispatch(self, event_name: str, *args, **kwargs):
        for func in self.extra_events.get(event_name, []):
            CallableAsync(func, loop=self.loop)(*args, **kwargs)

    def add_listener(self, func, name: str = MISSING):
        name = func.__name__ if name is MISSING else name

        self.extra_events[name] = self.extra_events.get(name, [])
        self.extra_events[name].append(func)

    def listen(self):
        self
