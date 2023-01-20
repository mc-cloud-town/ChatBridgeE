from typing import Union
import socketio

from mcdreforged.api.all import Info, PluginServerInterface, new_thread

sio: socketio.Client = None


@new_thread("chatbridge-send-data")
def send_event(event: str, data: Union[str, dict, list]):
    if sio is not None:
        sio.send(event, data)


@sio.event
def connect():
    print("connection established")


@sio.event
def disconnect():
    print("disconnected from server")


def on_load(server: PluginServerInterface, old_module):
    ...


def on_unload(server: PluginServerInterface):
    ...


def on_server_start(server: PluginServerInterface):
    ...


def on_server_startup(server: PluginServerInterface):
    ...


def on_server_stop(server: PluginServerInterface, return_code: int):
    ...


def on_info(server: PluginServerInterface, info: Info):
    ...


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    ...


def on_player_left(server: PluginServerInterface, player_name: str):
    ...


sio.connect("http://localhost:5000")
sio.wait()
