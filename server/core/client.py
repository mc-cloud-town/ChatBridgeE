# import socket
import asyncio
import signal

from server.utils.chat_bridge import BaseChatBridge, BaseState, ClientState


class ChatBridgeClient(BaseChatBridge, BaseState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _connect(self):
        self._sock.connect(self.server_address)

    async def start(self):
        async def login():
            while self.state not in [ClientState.STOPPED, ClientState.ONLINE]:
                await self._login()
                break

        self._connect()
        self.loop.create_task(login())
        await self.get_requests()

    def run(self):
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            loop.add_signal_handler(signal.SIGTERM, loop.stop)
        except (NotImplementedError, RuntimeError):
            pass

        def close(_):
            self.close()

        future = asyncio.ensure_future(self.start(), loop=loop)
        future.add_done_callback(close)

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            future.remove_done_callback(close)

    async def _login(self):
        await self.send_json(self._sock, {"name": "", "password": ""})

    async def get_requests(self):
        self.set_state(ClientState.CONNECTING)

        while True:
            try:
                print("data")
                data = await self.receive_data(self._sock)
            except UnicodeDecodeError:
                print("加密密鑰錯誤")
                continue
            print(data)

            if not data:
                self.close()
                break

            await self.send(self._sock, "pong")

            if type(data) != dict:
                continue

            ev: str = data.get("e")
            # da: Dict[str, str] = data.get("d")

            if self.state != ClientState.ONLINE and ev == "login_success":
                self.set_state(ClientState.ONLINE)
            elif ev == "message":
                # from_event = da.get("d")
                ...

            print(data)
        self.close()

    def close(self):
        self._sock.close()
        self.set_state(ClientState.DISCONNECTED)
