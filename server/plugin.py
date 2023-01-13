from importlib import util as import_util
import inspect
from types import ModuleType
from typing import Any, Callable, ClassVar, Optional, TypeVar, TYPE_CHECKING
from server.errors import ExtensionNotFound, PluginAlreadyLoaded, PluginNotFond

from server.utils import MISSING

if TYPE_CHECKING:
    from server.server import CoroFuncT, Server

PluginT = TypeVar("PluginT", bound="Plugin")


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

    def _inject(self, server: "PluginMixin") -> "Plugin":
        try:
            for name, method_name in self.__plugin_events__:
                server.add_listener(getattr(self, method_name), name)
        finally:
            try:
                self.on_load()
            except Exception:
                pass

        return self

    def _eject(self, sever: "Server") -> None:
        try:
            for _, method_name in self.__plugin_events__:
                sever.remove_listener(getattr(self, method_name))
        finally:
            try:
                self.on_load()
            except Exception:
                pass

    def on_load() -> None:
        pass

    def on_unload() -> None:
        pass

    @classmethod
    def listener(cls, name: str = MISSING) -> Callable[["CoroFuncT"], "CoroFuncT"]:
        def decorator(func: "CoroFuncT") -> "CoroFuncT":
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
        self.__extensions: dict[str, ModuleType] = {}
        self.__plugins: dict[str, Plugin] = {}

    def add_plugin(self, plugin: Plugin, *, override: bool = False) -> None:
        name = plugin.__plugin_name__

        if self.__plugins.get(name) is not None:
            if not override:
                raise PluginAlreadyLoaded(name)
            self.remove_plugin(name)

        plugin = plugin._inject(self)
        self.__plugins[name] = plugin

    def remove_plugin(self, name: str) -> Optional[Plugin]:
        if (plugin := self.__plugins.pop(name, None)) is not None:
            plugin._eject(self)

            return plugin

        return None

    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            return import_util.resolve_name(name, package)
        except ImportError:
            raise ExtensionNotFound(name)

    def load_plugin(self, name: str, package: Optional[str]) -> str:
        name = self._resolve_name(name, package)

        if name in self.__extensions:
            raise PluginAlreadyLoaded(name)
        # is not fond
        elif (spec := import_util.find_spec(name)) is None:
            raise PluginNotFond(name)
        elif spec.has_location:
            self
