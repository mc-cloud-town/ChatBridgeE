from typing import Any, Optional


class ChatBridgeEError(Exception):
    pass


class ExtensionError(ChatBridgeEError):
    def __init__(self, msg: Optional[str] = None, *args: Any) -> None:
        super().__init__(msg, *args)


class ExtensionNotFound(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} could not be found.")


class NoEntryPointError(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} there is no program entry point.")


class ExtensionAlreadyLoaded(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} is loaded repeatedly.")


class ExtensionPluginNotFond(ExtensionError):
    pass
