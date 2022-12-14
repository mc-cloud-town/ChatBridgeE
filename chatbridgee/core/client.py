import logging
from enum import Enum, auto
from threading import Event, RLock
from typing import Any, Dict, List, Optional, ParamSpec, TypeVar, Union

import socketio

from chatbridgee.utils.events import Events, event
from chatbridgee.core.structure import PayloadSender, PayloadStructure

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
    events_structure: Dict[str, PayloadSender] = {}

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
            call_listeners("connect", *args, **kwargs)

        @sio.on("connect_error")
        def on_connect_error(*args, **kwargs):
            self.stop()
            call_listeners("connect_error", *args, **kwargs)

        @sio.on("disconnect")
        def on_disconnect(*args, **kwargs):
            self._set_status(ClientStatus.DISCONNECTED)
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

    def get_structure(self, event: str) -> Union[PayloadSender, None]:
        return self.events_structure.get(event, None)

    def add_event_structure(self, name: str, structure: PayloadSender) -> None:
        self.events_structure[name] = structure

    def set_event_structure(self, structures: Dict[str, PayloadSender]) -> None:
        self.events_structure = structures

    def call(
        self,
        event: str,
        data: Optional[Union[PayloadSender, Any]] = None,
        namespace: Optional[str] = None,
        timeout: int = 60,
        receivers: Optional[List[str]] = None,
    ):
        return self.sio.call(
            event=event,
            data=PayloadStructure(
                event_name=event,
                data=data
                if (structure := self.get_structure(event)) is None or structure == -1
                else structure(data),
                receivers=[] if receivers is None else receivers,
            ),
            namespace=namespace,
            timeout=timeout,
        )

    # ----------------

    def get_name(self) -> str:
        return self.__name

    def stop(self) -> None:
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
        log.info(f"Started client {self.get_name()}")
        self.sio.connect(self._server_url)
        self.__connection_done.set()

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
