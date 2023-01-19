import inspect
import logging
import sys
from importlib import machinery as import_machine
from importlib import util as import_util
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Optional, TypeVar

from server.errors import ExtensionNotFound, PluginAlreadyLoaded, PluginNotFond
from server.utils import MISSING

if TYPE_CHECKING:
    from server.core.server import BaseServer, CoroFuncT

__all__ = ("Plugin", "PluginMixin")
PluginT = TypeVar("PluginT", bound="Plugin")

log = logging.getLogger("chat-bridgee")


class PluginMeta(type):
    __plugin_name__: str
    __plugin_description__: str
    __plugin_events__: dict[str, list[str]]  # (event_method_name, event_names)

    def __new__(cls: type["PluginMeta"], *args: Any, **kwargs: Any) -> "PluginMeta":
        name, bases, attrs = args

        attrs["__plugin_name__"] = kwargs.pop("name", name)
        attrs["__plugin_description__"] = kwargs.pop(
            "description",
            inspect.cleandoc(attrs.get("__doc__", "")),
        )

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
        events: dict[str, list[str]] = {}

        for base in reversed(new_cls.__mro__):
            for name, func in base.__dict__.items():
                # check is plugin listener
                # from Plugin.listener set
                if inspect.iscoroutinefunction(func) or getattr(
                    func,
                    "__plugin_listener__",
                    False,
                ):
                    events[name] = getattr(
                        func,
                        "__event_name__",
                        name,
                    ).split(" ")

        new_cls.__plugin_events__ = events

        return new_cls


class Plugin(metaclass=PluginMeta):
    __plugin_name__: ClassVar[str]
    __plugin_description__: ClassVar[str]
    __plugin_events__: ClassVar[dict[str, list[str]]]

    def __init__(self, server: "BaseServer") -> None:
        self.server = server

    def _inject(self, server: "BaseServer") -> "Plugin":
        try:
            for name, method_names in self.__plugin_events__.items():
                for method_name in method_names:
                    server.add_listener(getattr(self, method_name), name)
        finally:
            server.log.info(f"加載插劍: {self.__plugin_name__}")
            try:
                self.on_load()
            except Exception:
                pass

        return self

    def _eject(self, sever: "BaseServer") -> None:
        try:
            for method_names in self.__plugin_events__.values():
                for method_name in method_names:
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

    @property
    def plugins(self) -> dict[str, Plugin]:
        return self.__plugins

    def add_plugin(self, plugin: Plugin, *, override: bool = False) -> None:
        name = plugin.__plugin_name__

        if self.get_plugin(name) is not None:
            if not override:
                log.error(f"加載到相同名稱的插劍 {name}")
                raise PluginAlreadyLoaded(name)
            self.remove_plugin(name)

        plugin = plugin._inject(self)
        self.__plugins[name] = plugin

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self.__plugins.get(name)

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

    def load_plugin(
        self,
        name: str,
        package: Optional[str] = None,
        recursive: bool = False,
    ) -> None:
        name = self._resolve_name(name, package)

        if name in self.__extensions:
            raise PluginAlreadyLoaded(name)
        # is not fond
        elif (spec := import_util.find_spec(name)) is None:
            raise PluginNotFond(name)
        elif spec.has_location:
            self._load_from_module_spec(spec, name)
        else:
            path = Path(*name.split("."))
            glob_mod = path.rglob if recursive else path.glob

            for file in glob_mod("[!_]*.py"):
                self.load_plugin(
                    ".".join([*file.parts[:-1], file.stem]),
                    package=package,
                    recursive=recursive,
                )

    def _load_from_module_spec(self, spec: import_machine.ModuleSpec, key: str) -> None:
        lib = import_util.module_from_spec(spec)
        sys.modules[key] = lib

        try:
            spec.loader.exec_module(lib)
        except Exception as e:
            del sys.modules[key]
            print(e)
            # TODO add error
            return

        if (setup := getattr(lib, "setup", None)) is None:
            # TODO use NoEntryPointError error
            del sys.modules[key]
            raise ExtensionNotFound(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            # TODO add remove from add_plugin call cache
        else:
            self.__extensions[key] = lib
