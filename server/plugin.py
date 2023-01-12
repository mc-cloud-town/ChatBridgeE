from importlib import util as import_util


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
