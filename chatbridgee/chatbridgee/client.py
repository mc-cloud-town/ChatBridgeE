from pathlib import Path
from typing import Union

import socketio
from mcdreforged.api.all import (
    CommandSource,
    Info,
    Literal,
    PluginServerInterface,
    RTextBase,
    ServerInterface,
    new_thread,
)

from chatbridgee.chatbridgee.config import ChatBridgeEConfig

from .read import ReadClient

META = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
sio = socketio.Client()


def tr(key: str, *args, **kwargs) -> RTextBase:
    return ServerInterface.get_instance().rtr(f"{META.id}.{key}", *args, **kwargs)


@new_thread("chatbridge-send-data")
def send_event(event: str, data: Union[str, dict, list] = None):
    if sio.connected:
        sio.call(event, data)


@sio.event
def connect():
    print("connection established")


@sio.event
def disconnect():
    print("disconnected from server")


def display_help(source: CommandSource):
    source.reply(tr("help_message", version=META.version, prefix="!!cbe"))


def on_load(server: PluginServerInterface, old_module):
    config_path = Path(server.get_data_folder()) / "config.json"

    if not config_path.is_file():
        server.save_config_simple(ChatBridgeEConfig.get_default())

    try:
        server.load_config_simple(
            file_name=config_path,
            in_data_folder=False,
            target_class=ChatBridgeEConfig,
        )
    except:  # noqa: E722
        server.logger.exception(
            "Failed to read the config file! ChatBridgeE might not work properly"
        )
        server.logger.error("Fix the configure file and then reload the plugin")

    ReadClient(server, sio)

    server.register_help_message("!!cbe", tr("help_summary"))
    server.register_command(Literal("!!cbe").runs(display_help))

    @new_thread("chatbridge-start")
    def start():
        # TODO add config
        sio.connect(
            "http://localhost:8080",
            auth={
                "name": "surver",
                "password": "test",
            },
        )
        sio.wait()

    start()


@new_thread("chatbridge-disconnect")
def on_unload(server: PluginServerInterface):
    sio.disconnect()


def on_server_start(server: PluginServerInterface):
    send_event("server_start")


def on_server_startup(server: PluginServerInterface):
    send_event("server_startup")


def on_server_stop(server: PluginServerInterface, return_code: int):
    send_event("server_stop")


def on_info(server: PluginServerInterface, info: Info):
    if info.is_user and info.is_from_server:
        send_event("player_chat", [info.player, info.content])


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    send_event("player_joined", player_name)


def on_player_left(server: PluginServerInterface, player_name: str):
    send_event("player_left", player_name)
