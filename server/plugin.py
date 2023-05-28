from __future__ import annotations

import inspect
import logging
import sys
from enum import Enum, auto
from importlib import util as import_util
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Optional, Self, Type

from .errors import ExtensionAlreadyLoaded, ExtensionNotFound, NoEntryPointError
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
            server.log.info(f"加載插劍: [{self.__module__}] {self.__plugin_name__}")
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
    def __init__(self) -> None:
        self.__plugins: dict[str, Plugin] = {}
        self.__setup: dict[str, SoloSetup] = {}

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

        self.__plugins[name] = plugin._inject(self)

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self.__plugins.get(name)

    def remove_plugin(self, name: str) -> Optional[Plugin]:
        if (plugin := self.__plugins.pop(name, None)) is not None:
            plugin._eject(self)

        return plugin

    def load_extension(self, name: str | Path | SoloSetup) -> None:
        self.load_from_setup(self.setup_from_name(name))

    def unload_extension(self, name: str | Path | SoloSetup) -> None:
        name = self.setup_from_name(name)
        if (module := self.__setup.pop(name.name, None)) is None:
            raise ExtensionNotFound(name)

        for plugin_name, plugin in self.__plugins.copy().items():
            if _is_submodule(module.name, plugin.__module__):
                self.remove_plugin(plugin_name)

        module.unload(self)

    def setup_from_name(self, name: str | Path | SoloSetup) -> SoloSetup:
        if isinstance(name, SoloSetup):
            return name

        if isinstance(name, Path):
            if name.is_file() and name.suffix == ".py":
                return SoloSetup(fix_name(name))
            elif (name / "main.py").is_file():
                return SoloSetup(
                    f"{'.'.join(name.parts)}.main",
                    type=SoloSetupType.MODULE,
                )
            else:
                raise ExtensionNotFound(name)
        else:
            return SoloSetup(name)

    def load_from_setup(self, setup: SoloSetup) -> None:
        if setup.name in self.__setup:
            raise ExtensionAlreadyLoaded(setup.name)
        setup.load(self)
        self.__setup[setup.name] = setup

    @property
    def setups(self):
        return self.__setup


def fix_name(name: str | Path) -> str:
    return str(name).removesuffix(".py").replace("/", ".").replace("\\", ".")


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(f"{parent}.")


class SoloSetupType(Enum):
    FILE = auto()
    MODULE = auto()


class SoloSetup:
    setup: Callable[["BaseServer"], None] | None = None
    teardown: Callable[["BaseServer"], None] | None = None

    def __init__(
        self,
        name: Path | str,
        type: SoloSetupType = SoloSetupType.FILE,
    ) -> None:
        self.raw_name = self.name = name
        self.type = type

    def _resolve_name(self, name: str, package: Optional[str] = None) -> str:
        try:
            return import_util.resolve_name(name, package)
        except ImportError:
            raise ExtensionNotFound(name)

    def _module_from_spec(self, spec: ModuleSpec, name: str):
        lib = import_util.module_from_spec(spec)
        sys.modules[name] = lib
        spec.loader.exec_module(lib)
        return lib

    def _setup_module(self, module: ModuleType) -> None:
        self.setup = getattr(module, "setup", None)
        self.teardown = getattr(module, "teardown", None)

        if self.setup is None:
            raise NoEntryPointError(module.__name__)

    def setup_func(self) -> None:
        name, spec = self.raw_name, None
        if isinstance(name, Path):
            self.name = str(name)

            spec = import_util.spec_from_file_location(self.name, name)
        else:
            self.name = self._resolve_name(self.name)

            if not (spec := import_util.find_spec(self.name)) or not spec.has_location:
                if not self.name.endswith(".main"):
                    self.name += ".main"
                    return self.setup_func()

        if spec:
            self._setup_module(self._module_from_spec(spec, self.name))
        else:
            raise ExtensionNotFound(self.name)

    def load(self, server: "BaseServer") -> None:
        self.setup_func()

        if self.setup:
            try:
                self.setup(server)
            except Exception as e:
                log.exception(e)

    def unload(self, server: "BaseServer") -> None:
        sys.modules.pop(self.name, None)

        for name in sys.modules.copy().keys():
            if self.type == SoloSetupType.MODULE:
                name = name.removesuffix(".main")
            if _is_submodule(self.name, name):
                log.debug(
                    f"Remove module {name!r} when unloading plugin {repr(self)}, "
                    f"success={sys.modules.pop(name, None)}"
                )

        if self.teardown:
            try:
                self.teardown(server)
            except Exception as e:
                log.exception(e)
