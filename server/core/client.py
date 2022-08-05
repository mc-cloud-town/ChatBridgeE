# import socket
from enum import Enum, auto

from server.utils.chat_bridge import BaseChatBridge


class ClientState(Enum):
    CONNECTING = auto()
    ONLINE = auto()
    DISCONNECTED = auto()
    STOPPED = auto()


class ChatBridgeClient(BaseChatBridge):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__state = ClientState.STOPPED

    @property
    def state(self) -> ClientState:
        return self.__state

    def set_state(self, state: ClientState) -> None:
        self.__state = state

    async def __connect(self):
        self.set_state(ClientState.CONNECTING)
        self._sock.connect(self.server_address)

    async def _connect_and_login(self):
        self.__connect()
        self.set_state(ClientState.ONLINE)
        ...

    async def close(self):
        self._sock.close()
        self.set_state(ClientState.ONLINE)


# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((HOST, PORT))

# while True:
#     outdata = input("please input message: ")
#     print("send: " + outdata)
#     outdata = struct.pack("I", len(outdata)) + outdata.encode()
#     print("outdata:", outdata)
#     s.send(outdata)

#     indata = s.recv(1024)
#     print(indata)
#     if len(indata) == 0:  # connection closed
#         s.close()
#         print("server closed connection.")
#         break
#     print("recv: " + indata.decode())
