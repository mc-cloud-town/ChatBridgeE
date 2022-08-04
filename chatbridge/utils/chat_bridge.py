import socket

# from threading import RLock


class BaseChatBridge:
    def __init__(self):
        # TCP connect && server to server
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.__sock_lock = RLock()

    # def _set_socket(self, sock: Optional[socket.socket]):
    #     with self.__sock_lock:
    #         self._socket = sock

    # def __connect(self):
    #     sock = socket.socket()
    #     sock.connect(self.__server_address)


class ClientBaseChatBridge(BaseChatBridge):
    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_)
