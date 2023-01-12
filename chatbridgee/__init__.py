from pathlib import Path
import socketio

from mcdreforged.api.all import Info, PluginServerInterface, new_thread, CommandSource

from chatbridgee.core.structure import (
    ChatEventStructure,
    PlayerJoinedEventStructure,
    PlayerLeftEventStructure,
)


class MCDRClient(socketio.Client):
    def __init__(self, name: str):
        super().__init__(name)

    def on_command():
        ...


sio = socketio.Client()
sio = MCDRClient("test")


@new_thread("chatbridge-restart")
def restart_client(source: CommandSource):
    sio.stop()
    sio.start()


@new_thread("chatbridgee-load")
def on_load(server: PluginServerInterface, old_module):
    main()
    config_path = Path(server.get_data_folder()) / "config.json"
    if not config_path.is_file():
        server.save_config_simple({})


@new_thread("chatbridgee-unload")
def on_unload(server: PluginServerInterface):
    sio.stop()
    print("stop")


@new_thread("chatbridgee-server-start")
def on_server_start(server: PluginServerInterface):
    """伺服器啟動"""
    sio.call("server_start")


@new_thread("chatbridgee-server-startup")
def on_server_startup(server: PluginServerInterface):
    """伺服器啟動完成"""
    sio.call("server_startup")


@new_thread("chatbridgee-server-stop")
def on_server_stop(server: PluginServerInterface, return_code: int):
    """伺服器關閉"""
    sio.call("server_stop")


@new_thread("chatbridgee-info")
def on_info(server: PluginServerInterface, info: Info):
    try:
        time_message = f"{info.hour:0>2}:{info.min:0>2}:{info.sec:0>2}"
    except TypeError:
        time_message = "Invalid"

    if info.is_user and info.is_from_server:
        # on_chat
        return sio.call(
            "chat",
            ChatEventStructure(
                time=time_message,
                player=info.player,
                content=info.content,
            ),
        )


@new_thread("chatbridgee-player-joined")
def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    """玩家加入"""
    sio.call("player_joined", PlayerJoinedEventStructure(player_name=player_name))


@new_thread("chatbridgee-player-left")
def on_player_left(server: PluginServerInterface, player_name: str):
    """玩家離開"""
    sio.call("player_left", PlayerLeftEventStructure(player_name=player_name))


@new_thread
def main():
    sio.start()
    sio.wait()
