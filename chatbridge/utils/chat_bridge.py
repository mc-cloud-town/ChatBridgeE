import json
import socket
import struct
import asyncio
from typing import Any, Union

from chatbridge.utils.base import Address, AESCryptor


RECEIVE_BUFFER_SIZE = 1024


class EmptyContent(socket.error):
    pass


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
        if type(data) is not bytes:
            data = data.encode()
        encrypt = self.cryptor.encrypt(data)
        await self.loop.sock_sendall(client, struct.pack("I", len(encrypt)) + encrypt)

    async def receive_data(self, client: socket.socket) -> str:
        request = await self.loop.sock_recv(client, 4)

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

        return self.cryptor.decrypt(encrypted_data)
