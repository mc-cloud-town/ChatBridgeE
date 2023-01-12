from importlib import util as import_util
import inspect
from typing import Any, Callable, ClassVar, TypeVar

from server.utils import MISSING

PluginT = TypeVar("PluginT", bound="Plugin")
FuncT = TypeVar("FuncT", bound=Callable[..., Any])


class PluginMeta(type):
    __plugin_name__: str
    __plugin_description__: str
    __plugin_events__: tuple[str, list[str]]  # (event_method_name, event_names)

    def __new__(cls: type["PluginMeta"], *args: Any, **kwargs: Any) -> "PluginMeta":
        name, bases, attrs = args

        attrs["__plugin_name__"] = kwargs.pop("name", name)
        attrs["__plugin_description__"] = kwargs.pop(
            "description",
            inspect.cleandoc(attrs.get("__doc__", "")),
        )

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
        events: tuple[str, list[str]] = {}

        for base in reversed(new_cls.__mro__):
            for name, func in base.__dict__.items():
                # check is plugin listener
                # from Plugin.listener set
                if inspect.iscoroutinefunction(func) or getattr(
                    func,
                    "__plugin_listener__",
                    False,
                ):
                    events[name] = getattr(func, "__event_name__", name).split(" ")

        new_cls.__plugin_events__ = events

        return new_cls


class Plugin(metaclass=PluginMeta):
    __plugin_name__: ClassVar[str]
    __plugin_description__: ClassVar[str]
    __plugin_events__: ClassVar[tuple[str, list[str]]]

    # TODO inject
    def _inject(self):
        ...

    # TODO eject
    def _eject(self):
        ...

    @classmethod
    def listener(cls, name: str = MISSING) -> Callable[[FuncT], FuncT]:
        def decorator(func: FuncT) -> FuncT:
            # shallow copy
            actual = func

            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Listeners must be coroutines")

            if name is not MISSING:
                setattr(actual, name, actual)

            # as `actual.__plugin_listener__ = True`
            setattr(actual, "__plugin_listener__", True)

            return func

        return decorator


class PluginMixin:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def add_plugin(self, plugin):
        ...

    def _resolve_name(self, name: str, package: str | None) -> str:
        try:
            return import_util.resolve_name(name, package)
        except ImportError:
            # raise ExtensionNotFound(name)
            ...

    def load_plugin(self, name: str):
        ...
