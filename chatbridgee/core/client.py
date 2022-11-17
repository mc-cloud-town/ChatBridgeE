import logging
from enum import Enum, auto
from threading import Event, RLock
from typing import ParamSpec, TypeVar

import socketio

from chatbridgee.utils.events import Events, event

__all__ = ("BaseClient", "event")

log = logging.getLogger("chatbridgee")

R = TypeVar("R")
P = ParamSpec("P")


class ClientStatus(Enum):
    CONNECTING = auto()
    CONNECTED = auto()
    ONLINE = auto()
    DISCONNECTED = auto()
    STOPPED = auto()


class BaseClient(Events):
    def __init__(self, name: str):
        super().__init__()

        self.__name = name
        self.log = log

        self.sio = socketio.Client()
        self.__start_stop_lock = RLock()
        self.__connection_done = Event()
        self.status = ClientStatus.STOPPED
        self._server_url = "http://localhost:6000"

        self.handle_events()

    def handle_events(self) -> None:
        sio = self.sio

        @sio.on("*")
        def call_listeners(ev_name: str, *args, **kwargs):
            self.dispatch(ev_name, *args, **kwargs)

        @sio.on("connect")
        def on_connect(*args, **kwargs):
            self._set_status(ClientStatus.CONNECTED)
            print("connect")
            call_listeners("connect", *args, **kwargs)

        @sio.on("connect_error")
        def on_connect_error(*args, **kwargs):
            self.stop()
            call_listeners("connect_error", *args, **kwargs)

        @sio.on("disconnect")
        def on_disconnect(*args, **kwargs):
            self._set_status(ClientStatus.DISCONNECTED)
            print("disconnect")
            call_listeners("disconnect", *args, **kwargs)

    # ----------------
    # ---- status ----
    # ----------------
    def _has_status(self, status: ClientStatus) -> bool:
        return self.status == status

    def is_online(self) -> bool:
        return self._has_status(ClientStatus.ONLINE)

    def is_connecting(self) -> bool:
        return self._has_status(ClientStatus.CONNECTING)

    def is_connected(self) -> bool:
        return self._has_status(ClientStatus.CONNECTED) or self.is_online()

    def is_disconnected(self) -> bool:
        return self._has_status(ClientStatus.DISCONNECTED)

    def is_stopped(self) -> bool:
        return self._has_status(ClientStatus.STOPPED)

    def is_running(self) -> bool:
        return not self.is_stopped()

    def call(self, *args, **kwargs):
        # TODO add return
        return self.sio.call(*args, **kwargs)

    # ----------------

    def get_name(self) -> str:
        return self.__name

    def stop(self) -> None:
        self.sio.disconnect()
        with self.__start_stop_lock:
            if not self.is_running():
                log.warning("Client is not running, cannot stop")
                return
            self.__disconnect()
        self._set_status(ClientStatus.STOPPED)
        log.info("Stop client")

    def set_url(self, url: str):
        self._server_url = url

    def get_url(self) -> str:
        return self._server_url

    def start(self) -> None:
        log.info(f"Starting client {self.get_name()}")

        with self.__start_stop_lock:
            if self.is_running():
                log.warning("Client is running, cannot start again")
                return
            self._set_status(ClientStatus.CONNECTING)

        self.__connection_done.clear()
        self.sio.connect(self._server_url)
        self.__connection_done.set()

        log.info(f"Started client {self.get_name()}")

    def __disconnect(self) -> None:
        if not self.is_running:
            return
        self.sio.disconnect()
        self._set_status(ClientStatus.DISCONNECTED)

    def _set_status(self, status: ClientStatus) -> None:
        self.status = status
        log.debug(f"Client {self.get_name()} change status: {status}")

    def wait(self) -> None:
        self.sio.wait()
