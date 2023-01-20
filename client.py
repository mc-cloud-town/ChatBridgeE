from typing import Union

import socketio
from mcdreforged.api.all import Info, PluginServerInterface, new_thread

sio = socketio.Client()

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


@new_thread("chatbridge-start")
def on_load(server: PluginServerInterface, old_module):
    sio.connect("http://localhost:8080")
    sio.wait()


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
    ...


def on_player_joined(server: PluginServerInterface, player_name: str, info: Info):
    send_event("player_joined", player_name)


def on_player_left(server: PluginServerInterface, player_name: str):
    send_event("player_left", player_name)
