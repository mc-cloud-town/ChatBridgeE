import json
import socket
from typing import Any, Dict, List, Union

from server.errors.http import EmptyContent
from server.utils.chat_bridge import BaseChatBridge


MAX_CONNECTIONS = 5
RECEIVE_BUFFER_SIZE = 1024


class ChatBridgeServerClient:
    ...


class ChatBridgeServer(BaseChatBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients: Dict[str, socket.socket] = {}

    def to_bytes(self, data: Union[bytes, str, Dict[Any, Any], List[Any]]) -> bytes:
        if type(data) == bytes:
            return data
        bytes_str: str = data
        if type(data) in [list, dict]:
            bytes_str = json.dumps(data)
        return bytes_str.encode()

    async def send(self, client: socket.socket, data: Union[bytes, str]):
        await self.loop.sock_sendall(client, self.to_bytes(data))

    async def send_all(
        self,
        data: Union[bytes, str],
        exclude: List[socket.socket] = [],
    ):
        for client in self.clients:
            if client in exclude:
                self.loop.sock_sendall(client, data)

    async def handle_client(self, client: socket.socket):
        while True:
            try:
                data = await self.receive_data(client)
            except EmptyContent:
                continue

            if not data:
                break

            print(data)

        client.close()

    async def run_server(self):
        loop = self.loop
        server = self._sock
        self.server = server
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(self.server_address)
        server.listen(MAX_CONNECTIONS)
        server.settimeout(5)
        server.setblocking(False)

        while True:
            try:
                client, _ = await loop.sock_accept(server)
                print(_)
            except socket.timeout:
                continue
            loop.create_task(self.handle_client(client))

    def start(self):
        try:
            self.loop.run_until_complete(self.run_server())
        except KeyboardInterrupt:
            self.server.close()

    def stop(self):
        self.server.close()
        self.loop.close()
