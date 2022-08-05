import socket
import asyncio
import struct
from typing import Union

from chatbridge.utils.chat_bridge import BaseChatBridge


MAX_CONNECTIONS = 5
RECEIVE_BUFFER_SIZE = 1024


class EmptyContent(socket.error):
    pass


class ChatBridgeServerClient:
    ...


class ChatBridgeServer(BaseChatBridge):
    async def send(self, client: socket.socket, data: Union[bytes, str]):
        if type(data) is not bytes:
            data = data.encode()
        await self.loop.sock_sendall(client, data)

    async def handle_client(self, client: socket.socket):
        loop = asyncio.get_event_loop()
        request = None
        while request != "quit":
            request = await loop.sock_recv(client, 4)

            if len(request) < 4:
                print("訊息格式錯誤")
                continue

            remaining_data_length = struct.unpack("I", request)[0]
            encrypted_data = bytes()

            while remaining_data_length > 0:
                buf = await loop.sock_recv(
                    client,
                    min(remaining_data_length, RECEIVE_BUFFER_SIZE),
                )
                encrypted_data += buf
                remaining_data_length -= len(buf)

            await self.send(client, encrypted_data)

        client.close()

    async def run_server(self):
        loop = self.loop
        server = self._sock
        self.server = server

        server.bind(self.server_address)
        server.listen(MAX_CONNECTIONS)
        server.settimeout(5)
        server.setblocking(False)

        while True:
            try:
                client, _ = await loop.sock_accept(server)
            except socket.timeout:
                continue
            loop.create_task(self.handle_client(client))

    def start(self):
        try:
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.run_server())
        except KeyboardInterrupt:
            self.server.close()

    def stop(self):
        self.server.close()
        self.loop.close()
