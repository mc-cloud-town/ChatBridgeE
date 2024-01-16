from .core.server import BaseServer, CoroFuncT
from .utils.config import Config
from _typeshed import Incomplete
from enum import Enum
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, ClassVar, Optional, Type, TypeVar

T = TypeVar('T', bound='Plugin')

class PluginMeta(type):
    __plugin_name__: str
    __plugin_description__: str
    __plugin_events__: dict[str, list[str]]
    def __new__(cls, *args: Any, **kwargs: Any) -> PluginMeta: ...

class Plugin(metaclass=PluginMeta):
    __plugin_name__: ClassVar[str]
    __plugin_description__: ClassVar[str]
    __plugin_events__: ClassVar[dict[str, list[str]]]
    __plugin_config__: ClassVar[Optional[Type[Config]]]
    server: Incomplete
    loop: Incomplete
    server_config: Incomplete
    log: Incomplete
    console: Incomplete
    config: Incomplete
    def __init__(self, server: BaseServer) -> None: ...
    def _inject(self, server: BaseServer) -> T: ...
    def _eject(self, server: BaseServer) -> None: ...
    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
    def on_unload_before(self) -> None: ...
    @classmethod
    def listener(cls, name: str | CoroFuncT = ...) -> Callable[[CoroFuncT], CoroFuncT]: ...

class PluginMixin:
    __plugins: Incomplete
    __setup: Incomplete
    def __init__(self) -> None: ...
    @property
    def plugins(self) -> dict[str, Plugin]: ...
    def add_plugin(self, plugin: Plugin, *, override: bool = ...) -> None: ...
    def get_plugin(self, name: str) -> Optional[Plugin]: ...
    def remove_plugin(self, name: str) -> Optional[Plugin]: ...
    def load_extension(self, name: str | Path | SoloSetup) -> None: ...
    def unload_extension(self, name: str | Path | SoloSetup) -> None: ...
    def setup_from_name(self, name: str | Path | SoloSetup) -> SoloSetup: ...
    def load_from_setup(self, setup: SoloSetup) -> None: ...
    @property
    def setups(self): ...

class SoloSetupType(Enum):
    FILE: Incomplete
    MODULE: Incomplete

class SoloSetup:
    setup: Callable[[BaseServer], None] | None
    teardown: Callable[[BaseServer], None] | None
    raw_name: Incomplete
    type: Incomplete
    def __init__(self, name: Path | str, type: SoloSetupType = ...) -> None: ...
    def _resolve_name(self, name: str, package: Optional[str] = ...) -> str: ...
    def _module_from_spec(self, spec: ModuleSpec, name: str): ...
    def _setup_module(self, module: ModuleType) -> None: ...
    name: Incomplete
    def setup_func(self) -> None: ...
    def load(self, server: BaseServer) -> None: ...
    def unload(self, server: BaseServer) -> None: ...
