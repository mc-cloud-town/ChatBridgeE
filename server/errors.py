from typing import Any, Optional


class ChatBridgeEError(Exception):
    pass


class ExtensionError(ChatBridgeEError):
    """插件錯誤"""

    def __init__(self, msg: Optional[str] = None, *args: Any, name: str) -> None:
        self.name = name
        super().__init__(msg, *args)


class ExtensionNotFound(ExtensionError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} could not be found.", name=name)


class PluginAlreadyLoaded(ExtensionError):
    """插件已加載"""

    pass


class PluginNotFond(ExtensionError):
    """插件未找到"""

    pass
