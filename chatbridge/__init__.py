from pathlib import Path

import socketio
from mcdreforged.api.all import PluginServerInterface, Info, new_thread


sio = socketio.Client()


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
    sio.emit("server_start")


def on_server_startup(server: PluginServerInterface):
    """伺服器啟動完成"""
    sio.emit("server_startup")


def on_server_stop(server: PluginServerInterface, return_code: int):
    """伺服器關閉"""
    sio.emit("server_stop")


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    """玩家加入"""
    sio.emit(
        "player_joined",
    )


def on_player_left(server: PluginServerInterface, player_name: str):
    """玩家離開"""
    sio.emit("player_left", player_name)


@sio.event
async def connect():
    print("連線完成")


@sio.event
async def disconnect():
    print("與伺服器斷開連線")


@new_thread
def main():
    sio.connect("http://localhost:6000", {"username": "user", "password": "password_"})
