class ChatBridgeEError(Exception):
    pass


class PluginError(ChatBridgeEError):
    """插件錯誤"""

    pass


class ExtensionNotFound(PluginError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Extension {name!r} could not be found.", name=name)


class PluginAlreadyLoaded(PluginError):
    """插件已加載"""

    pass


class PluginNotFond(PluginError):
    """插件未找到"""

    pass
