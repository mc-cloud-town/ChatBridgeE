from pathlib import Path

from mcdreforged.api.all import PluginServerInterface, Info


# new_thread


def on_load(server: PluginServerInterface, old_module):
    config_path = Path(server.get_data_folder()) / "config.json"
    if not config_path.is_file():
        server.save_config_simple({})


def on_unload(server: PluginServerInterface):
    ...


def on_info(server: PluginServerInterface, info: Info):
    if info.is_user:
        ...
    elif info.is_from_server:
        ...


def on_server_start(server: PluginServerInterface):
    """伺服器啟動"""
    ...


def on_server_startup(server: PluginServerInterface):
    """伺服器啟動完成"""
    ...


def on_server_stop(server: PluginServerInterface, return_code: int):
    """伺服器關閉"""
    ...


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    """玩家加入"""
    ...


def on_player_left(server: PluginServerInterface, player_name: str):
    """玩家離開"""
    ...
