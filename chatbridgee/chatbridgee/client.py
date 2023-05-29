import time
from pathlib import Path
from threading import Lock
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
from socketio import exceptions

from .config import ChatBridgeEConfig
from .read import ReadClient

META = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()
sio = socketio.Client()
cb_lock = Lock()

config: ChatBridgeEConfig = None


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


def parse_properties(path: Path | str) -> dict:
    path = Path(path) / "server.properties"
    if not path.is_file():
        return {}

    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue

        key, value = line.split("=", maxsplit=1)
        result[key] = value

    return result


def on_load(server: PluginServerInterface, old_module):
    config_path = Path(server.get_data_folder()) / "config.json"

    if not config_path.is_file():
        server.save_config_simple(ChatBridgeEConfig.get_default())

    try:
        global config
        config = server.load_config_simple(
            file_name=config_path,
            in_data_folder=False,
            target_class=ChatBridgeEConfig,
        )
    except:  # noqa: E722
        server.logger.exception(
            "Failed to read the config file! ChatBridgeE might not work properly"
        )
        server.logger.error("Fix the configure file and then reload the plugin")

    ReadClient(server, sio, config)

    auth_else = {}
    directory = server.get_mcdr_config().get("working_directory", "server")
    if (mc_config := parse_properties(directory)).get("enable-rcon"):
        auth_else["rcon"] = {
            k: v
            for k, v in {
                "ip": mc_config.get("rcon.ip"),
                "port": mc_config.get("rcon.port"),
                "password": mc_config.get("rcon.password"),
            }.items()
            if v is not None
        }

    server.register_help_message("!!cbe", tr("help_summary"))
    server.register_command(Literal("!!cbe").runs(display_help))

    @new_thread("chatbridge-start")
    def start():
        with cb_lock:
            auth = config.client_info
            try:
                sio.connect(
                    f"http://{config.server_address}",
                    auth={"name": auth.name, "password": auth.password, **auth_else},
                )
                sio.wait()
            except exceptions.ConnectionError:
                server.logger.error(f"無法連接到 {config.server_address}\n五秒後重試")
                time.sleep(5)
                start()
            except TimeoutError:
                server.logger.error(f"連線到 {config.server_address} 超時\n五秒後重試")
                time.sleep(5)
                start()

    start()


@new_thread("chatbridge-disconnect")
def on_unload(server: PluginServerInterface):
    with cb_lock:
        sio.disconnect()


def on_server_start(server: PluginServerInterface):
    send_event("server_start")


def on_server_startup(server: PluginServerInterface):
    send_event("server_startup")


def on_server_stop(server: PluginServerInterface, return_code: int):
    send_event("server_stop")


def on_info(server: PluginServerInterface, info: Info):
    if info.is_user and info.is_from_server:
        if info.player in config.chat_blacklist_names:
            return

        send_event("player_chat", [info.player, info.content])


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    send_event("player_joined", player_name)


def on_player_left(server: PluginServerInterface, player_name: str):
    send_event("player_left", player_name)
