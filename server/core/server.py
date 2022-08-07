import json
import socket
import asyncio
from typing import Any, Dict, List, Union

from server.errors.http import EmptyContent
from server.utils.chat_bridge import BaseChatBridge, ClientState, BaseState


MAX_CONNECTIONS = 5
RECEIVE_BUFFER_SIZE = 1024


class ChatBridgeClient(BaseState):
    def __init__(self, server: "ChatBridgeServer"):
        super().__init__()

        self.server = server
        self.send = server.send
        self.receive_data = server.receive_data
        self.loop = server.loop
        self.name = None

    async def check_online_close(self):
        async def is_online():
            while self.state != ClientState.ONLINE:
                await asyncio.sleep(1)

        try:
            await asyncio.wait_for(is_online(), timeout=10.0)
        except asyncio.TimeoutError:
            print("登入超時")
            self.close()

    async def handle_client(self, client: socket.socket):
        while True:
            try:
                data = await self.receive_data(client)
            except UnicodeDecodeError:
                print("加密密鑰錯誤")
                continue
            except EmptyContent:
                continue
            except (ConnectionResetError, ConnectionAbortedError):
                print(f"{self.name} 連線中斷")
                break

            if not data:
                break

            print(data)

            try:
                await self.send(client, "pong")
            except OSError:
                break
        self.close()

    def close(self):
        self.client.close()

    async def __call__(self, client: socket.socket):
        self.client = client
        self.loop.create_task(self.check_online_close())
        await self.handle_client(client)


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
            if client not in exclude:
                await self.send(client, data)

    async def run_server(self):
        loop = self.loop
        server = self._sock
        self.server = server
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(self.server_address)
        server.listen(MAX_CONNECTIONS)
        server.settimeout(5)
        server.setblocking(False)
        print("server listening")

        while True:
            try:
                client, _ = await loop.sock_accept(server)
            except socket.timeout:
                continue
            loop.create_task(ChatBridgeClient(self)(client))

    def start(self):
        try:
            self.loop.run_until_complete(self.run_server())
        except KeyboardInterrupt:
            self.server.close()

    def stop(self):
        self.server.close()
        self.loop.close()
