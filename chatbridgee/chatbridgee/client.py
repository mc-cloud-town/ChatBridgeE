from typing import Union

import socketio
from mcdreforged.api.all import (
    CommandSource,
    Info,
    Literal,
    PluginServerInterface,
    new_thread,
    RTextBase,
    ServerInterface,
)

META = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
sio = socketio.Client()


def tr(key: str, *args, **kwargs) -> RTextBase:
    return ServerInterface.get_instance().rtr(f"{META.id}.{key}", *args, **kwargs)


@new_thread("chatbridge-send-data")
def send_event(event: str, data: Union[str, dict, list] = None):
    if sio is not None:
        sio.call(event, data)


@sio.event
def connect():
    print("connection established")


@sio.event
def disconnect():
    print("disconnected from server")


def display_help(source: CommandSource):
    source.reply(tr("help_message", version=META.version, prefix="!!cbe"))


def display_status(source: CommandSource):
    # source.reply(tr("help_message", version=META.version, prefix="!!cbe"))
    ...


def on_load(server: PluginServerInterface, old_module):
    server.register_help_message("!!cbe", tr("help_summary"))
    server.register_command(
        Literal("!!cbe").runs(display_help)
        # .then(Literal("status"))
        # .runs(display_status),
    )

    @new_thread("chatbridge-start")
    def start():
        sio.connect("http://localhost:8080")
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
        send_event("player_chat", {"content": info.content, "player": info.player})


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    send_event("player_joined", player_name)


def on_player_left(server: PluginServerInterface, player_name: str):
    send_event("player_left", player_name)
