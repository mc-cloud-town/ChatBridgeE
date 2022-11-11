from typing import (
    Any,
    Dict,
    List,
    Tuple,
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

from chatbridgee.utils.utils import MISSING


R = TypeVar("R")
P = ParamSpec("P")


class EventHandler(Generic[P, R]):
    cls = None

    def __init__(self, func: Callable[P, R], event_name: Optional[str] = None) -> None:
        self.__func = func
        self.__name__ = func.__name__
        self.event_name = func.__name__ if event_name is None else event_name

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.__func(*args, **kwargs)

    def _set_cls(self, cls) -> None:
        self.cls = cls


# fmt: off
@overload  # noqa: E302
def event(arg: str) -> Callable[[Callable[P, R]], EventHandler[P, R]]: ...  # noqa: E704
@overload  # noqa: E302
def event(arg: Callable[P, R]) -> EventHandler[P, R]: ...  # noqa: E704
# fmt: on


def event(arg: Union[str, Callable[P, R]] = MISSING):
    if type(arg) == str:

        def decorator(func: Callable[P, R]):
            setattr(func, "__event_name__", arg)
            return event(func)

        return decorator

    return EventHandler(arg, getattr(arg, "__event_name__", arg.__name__))


class EventsMate(type):
    _class_events: List[Tuple[str, EventHandler]] = []

    def __new__(cls: Type["EventsMate"], *args: Any, **kwargs: Any) -> "EventsMate":
        name, bases, attrs = args

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        events = []

        for base in reversed(new_cls.__mro__):
            for _, func in base.__dict__.items():
                if not isinstance(func, EventHandler):
                    continue

                name = func.event_name
                events.append((name, func))

        new_cls._class_events = events

        return new_cls

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


class Events(metaclass=EventsMate):
    _class_events: ClassVar[List[Tuple[str, EventHandler]]] = {}

    def __init__(self) -> None:
        self.extra_events: Dict[str, List[EventHandler]] = {}

        for name, method in self._class_events:
            method._set_cls(self)
            self.add_listener(method, name)

    def dispatch(self, event_name: str, *args, **kwargs) -> None:
        for func in self.extra_events.get(event_name, []):
            if isinstance(func, EventHandler) and func.cls:
                args = (func.cls, *args)

            try:
                func(*args, **kwargs)
            except Exception as e:
                self.dispatch("dispatch_error", func, e)

    def add_listener(self, func: Callable, name: str = MISSING) -> None:
        name = func.__name__ if name is MISSING else name

        self.extra_events[name] = self.extra_events.get(name, [])
        self.extra_events[name].append(func)

    def listen(self, arg: Union[str, Callable] = MISSING, *args, **kwargs):
        name = arg

        def decorator(func: Callable):
            self.add_listener(func, name, *args, **kwargs)
            return func

        if callable(arg):
            name = arg.__name__
            return decorator(arg)

        return decorator
