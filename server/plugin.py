from __future__ import annotations

import importlib
import inspect
import logging
import sys
from importlib import util as import_util
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Optional, Self, Type

from .errors import (
    ExtensionAlreadyLoaded,
    ExtensionError,
    ExtensionNotFound,
    ExtensionPluginNotFond,
    NoEntryPointError,
)
from .utils import MISSING
from .utils.config import Config

if TYPE_CHECKING:
    from .core.server import BaseServer, CoroFuncT

__all__ = ("Plugin", "PluginMixin")

log = logging.getLogger("chat-bridgee")


class PluginMeta(type):
    __plugin_name__: str
    __plugin_description__: str
    __plugin_events__: dict[str, list[str]]  # (event_method_name, event_names)

    def __new__(cls: type["PluginMeta"], *args: Any, **kwargs: Any) -> "PluginMeta":
        name, bases, attrs = args

        attrs["__plugin_config__"] = kwargs.pop("config", None)
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
    __plugin_config__: ClassVar[Optional[Type[Config]]]

    def __init__(self, server: "BaseServer") -> None:
        self.server = server
        self.loop = server.loop
        self.server_config = server.config
        self.log = server.log
        self.config: Config = {}

        if self.__plugin_config__:
            self.config = self.__plugin_config__.load(_auto_create=True)

    def _inject(self, server: "BaseServer") -> "Self":
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

    def _eject(self, server: "BaseServer") -> None:
        try:
            self.on_unload_before()
        except Exception as e:
            log.error(f"插劍 {self.__plugin_name__} on_unload_before 出錯: {e}")
            pass

        try:
            for method_names in self.__plugin_events__.values():
                for method_name in method_names:
                    server.remove_listener(getattr(self, method_name))
        finally:
            try:
                self.on_unload()
            except Exception as e:
                log.error(f"插劍 {self.__plugin_name__} on_unload 出錯: {e}")
                pass

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass

    def on_unload_before(self) -> None:
        pass

    @classmethod
    def listener(
        cls,
        name: str | CoroFuncT = MISSING,
    ) -> Callable[[CoroFuncT], CoroFuncT]:
        def decorator(func: CoroFuncT) -> CoroFuncT:
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

        if inspect.iscoroutinefunction(name):
            name = (func := name).__name__
            return decorator(func)

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
                raise ExtensionAlreadyLoaded(name)
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

    def unload_extension(self, name: str, package: Optional[str] = None) -> None:
        name = self._resolve_name(name, package=package)

        if (module := self.__extensions.pop(name, None)) is None:
            raise ExtensionNotFound(name)

        for plugin_name, plugin in self.__plugins.copy().items():
            if _is_submodule(module.__name__, plugin.__module__):
                self.remove_plugin(plugin_name)

        self._module_finalizer(module, name)

    def _module_finalizer(self, lib: ModuleType, key: str) -> None:
        self.__extensions.pop(key, None)
        sys.modules.pop(key, None)

        for module in sys.modules.copy().keys():
            if _is_submodule(lib.__name__.removesuffix(".main"), module):
                log.debug(
                    f"Remove module {module} when unloading plugin {repr(self)}, "
                    f"success={sys.modules.pop(module, None)}"
                )

    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            return import_util.resolve_name(name, package)
        except ImportError:
            raise ExtensionNotFound(name)

    def load_plugin(
        self,
        name: str,
        package: Optional[str] = None,
        block_plugin: list[str] = [],
    ) -> None:
        name = self._resolve_name(name, package)

        if name in self.__extensions:
            raise ExtensionAlreadyLoaded(name)
        # is not fond
        elif (spec := import_util.find_spec(name)) is None:
            raise ExtensionPluginNotFond(name)
        elif spec.has_location:
            lib = import_util.module_from_spec(spec)
            sys.modules[name] = lib

            try:
                spec.loader.exec_module(lib)
            except Exception as e:
                del sys.modules[name]
                log.exception("loader exec module error", exc_info=e)
                return

            self.from_module_setup(lib, name)
        else:
            path = Path(*name.split("."))

            for file in path.glob("[!_]*"):
                if (pa := ".".join([*file.parts[:-1], file.stem])) in block_plugin:
                    continue

                if file.is_file() and file.suffix == ".py":
                    self.load_plugin(
                        pa,
                        package=package,
                        block_plugin=block_plugin,
                    )
                else:
                    self.from_module_setup(
                        importlib.import_module(f"{pa}.main", package)
                    )

    def from_module_setup(self, module: ModuleType, name: str | None = None) -> None:
        if name is None:
            name = module.__name__

        if (setup := getattr(module, "setup", None)) is None:
            del sys.modules[name]
            raise NoEntryPointError()

        try:
            setup(self)
        except Exception as e:
            del sys.modules[name]
            log.error(f"插劍加載失敗: {e}")
            raise ExtensionError(e, name="插劍加載失敗")
        else:
            self.__extensions[name] = module

    @property
    def extensions_catch(self):
        return self.__extensions


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(f"{parent}.")
