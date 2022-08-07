from enum import Enum, auto
import json
import socket
import struct
import asyncio
from typing import Any, Union, Literal

from server.errors.http import EmptyContent
from server.utils.base import Address, AESCryptor


RECEIVE_BUFFER_SIZE = 1024


class BaseChatBridge:
    def __init__(self, aes_key: str, server_address: Address):
        super().__init__()
        self.aes_key = aes_key
        self.server_address = server_address
        self.cryptor = AESCryptor(aes_key)
        self.loop = asyncio.get_event_loop()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    async def send_json(self, client: socket.socket, data: Any) -> None:
        await self.send(client, json.dumps(data, ensure_ascii=False))

    async def send(self, client: socket.socket, data: Union[bytes, str]) -> None:
        if type(data) is not str:
            data = data.decode("utf-8")
        encrypt = self.cryptor.encrypt(data)
        await self.loop.sock_sendall(client, struct.pack("I", len(encrypt)) + encrypt)

    async def receive_data(
        self,
        client: socket.socket,
    ) -> Union[str, Literal[False], dict, list]:
        request = await self.loop.sock_recv(client, 4)

        if request == b"":
            return False

        if len(request) < 4:
            raise EmptyContent("Error content received")

        remaining_data_length = struct.unpack("I", request)[0]
        encrypted_data = bytes()

        while remaining_data_length > 0:
            buf = await self.loop.sock_recv(
                client,
                min(remaining_data_length, RECEIVE_BUFFER_SIZE),
            )
            encrypted_data += buf
            remaining_data_length -= len(buf)

        data = self.cryptor.decrypt(encrypted_data)

        try:
            return json.loads(data)
        except:
            ...

        return data


class ClientState(Enum):
    CONNECTING = auto()
    ONLINE = auto()
    DISCONNECTED = auto()
    STOPPED = auto()


class BaseState:
    def __init__(self):
        self.__state = ClientState.STOPPED

    @property
    def state(self) -> ClientState:
        return self.__state

    def set_state(self, state: ClientState) -> None:
        self.__state = state

    def _in_status(self, *states: ClientState) -> bool:
        return self.__state in states

    def _is_connecting(self) -> bool:
        return self._in_status(ClientState.CONNECTING)

    def _is_online(self) -> bool:
        return self._in_status(ClientState.ONLINE)

    def _is_disconnected(self) -> bool:
        return self._in_status(ClientState.DISCONNECTED)

    def _is_stopped(self) -> bool:
        return self._in_status(ClientState.STOPPED)
