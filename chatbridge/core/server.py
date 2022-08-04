import socket
import asyncio

# from typing import Dict
from chatbridge.utils.base import Address
from chatbridge.utils.chat_bridge import BaseChatBridge


MAX_CONNECTIONS = 5


class ChatBridgeServerClient:
    ...


class ChatBridgeServer(BaseChatBridge):
    def __init__(self, aes_key: str, server_address: Address):
        super().__init__()
        self.aes_key = aes_key
        self.server_address = server_address
        self.loop = asyncio.get_event_loop()

    # async def handle_client(self, client):
    #     loop = self.loop
    #     request = None
    #     while request != "quit":
    #         request = (await loop.sock_recv(client, 255)).decode("utf8")
    #         print(request)
    #         await loop.sock_sendall(client, response.encode("utf8"))
    #     client.close()

    async def run_server(self):
        loop = self.loop
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server

        server.bind(self.server_address)
        server.listen(MAX_CONNECTIONS)
        server.setblocking(False)

        while True:
            client, _ = await loop.sock_accept(server)
            loop.create_task(self.handle_client(client))

    def start(self):
        try:
            self.loop.run_until_complete(self.run_server())
        except KeyboardInterrupt:
            self.server.close()

    def _loop(self):
        sock = self._sock
        sock.bind(self.server_address)
        sock.settimeout(3)
        sock.listen(MAX_CONNECTIONS)

        while True:
            try:
                client, addr = sock.accept()
            except socket.timeout:
                continue


# def handle_client(client):
#     request = None
#     while request != "quit":
#         request = client.recv(255).decode("utf8")
#         response = cmd.run(request)
#         client.send(response.encode("utf8"))
#     client.close()


# def run_server(server):
#     client, _ = server.accept()
#     handle_client(client)


# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.bind(("localhost", 15555))
# server.listen(8)

# loop = asyncio.get_event_loop()
# asyncio.async(run_server(server))
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     server.close()
