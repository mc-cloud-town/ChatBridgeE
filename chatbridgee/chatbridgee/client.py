import asyncio
import time
from pathlib import Path
from threading import Thread

from mcdreforged.api.all import (
    CommandSource,
    Info,
    Literal,
    PluginServerInterface,
    new_thread,
)
from socketio import exceptions

from .config import ChatBridgeEConfig
from .file_sync import FileSyncPlugin
from .plugin import META, tr
from .read import ReadClient
from .utils import Client

loop = asyncio.new_event_loop()
sio = Client(loop=loop)

config: ChatBridgeEConfig = None


@sio.event
async def connect():
    print("connection established")


@sio.event
async def disconnect():
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
        result[key.strip()] = value.strip()

    return result


def on_load(server: PluginServerInterface, old_module):
    config_path = Path(server.get_data_folder()) / "config.json"

    if not config_path.is_file():
        server.save_config_simple(ChatBridgeEConfig.get_default())
        return

    global config
    config = server.load_config_simple(
        file_name=config_path,
        in_data_folder=False,
        target_class=ChatBridgeEConfig,
    )

    ReadClient(server, sio, config)
    FileSyncPlugin(server, sio, config)

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

    async def runner():
        auth = config.client_info
        try:
            await sio.connect(
                f"http://{config.server_address}",
                auth={"name": auth.name, "password": auth.password, **auth_else},
            )
            await sio.wait()
        except exceptions.ConnectionError:
            server.logger.error(f"無法連接到 {config.server_address}\n五秒後重試")
            time.sleep(5)
            await runner()
        except TimeoutError:
            server.logger.error(f"連線到 {config.server_address} 超時\n五秒後重試")
            time.sleep(5)
            await runner()

    def run_forever():
        def stop_loop_on_completion(f):
            loop.stop()

        server.logger.info("loop started")
        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)

        try:
            loop.run_forever()
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            loop.close()
            server.logger.info("loop stopped")

    Thread(target=run_forever, name="chatbridge-loop_forever", daemon=True).start()


@new_thread("chatbridge-disconnect")
def on_unload(server: PluginServerInterface):
    loop.create_task(sio.disconnect())


def on_server_start(server: PluginServerInterface):
    sio.send_event("server_start")


def on_server_startup(server: PluginServerInterface):
    sio.send_event("server_startup")


def on_server_stop(server: PluginServerInterface, return_code: int):
    sio.send_event("server_stop")


def on_info(server: PluginServerInterface, info: Info):
    if info.is_user and info.is_from_server:
        if info.player in config.chat_blacklist_names:
            return

        sio.send_event("player_chat", [info.player, info.content])


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    sio.send_event("player_joined", player_name)


def on_player_left(server: PluginServerInterface, player_name: str):
    sio.send_event("player_left", player_name)
