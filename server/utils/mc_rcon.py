"""
https://developer.valvesoftware.com/wiki/Source_RCON_Protocol
"""

import asyncio
import struct
from asyncio import AbstractEventLoop, BaseTransport, Future, Lock, Protocol
from enum import Enum, auto
from typing import Self, TypedDict


class RconPacketType(Enum):
    COMMAND_RESPONSE = 0
    COMMAND_EXECUTE = 2
    LOGIN = 3


class RconPacketData(TypedDict):
    id: int
    type: int
    data: str


class ReconException(Exception):
    pass


class LoginError(ReconException):
    pass


class ConnectState(Enum):
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATED = auto()
    CLOSED = auto()


class RconClientProtocol(Protocol):
    def __init__(
        self,
        loop: AbstractEventLoop | None = None,
        command_timeout: int = 30,
    ):
        self.state = ConnectState.CONNECTING

        self._id = -1
        self._buffer = b""
        self._transport: BaseTransport | None = None
        self._loop = asyncio.get_running_loop() if loop is None else loop
        self._waiters = dict[str, Future[RconPacketData]]()
        self._lock = Lock()
        self.timeout = command_timeout

    def __call__(self) -> Self:
        return self

    async def _wait_receive(self, id: int = None):
        self._waiters[id] = self._loop.create_future()

        data = await self._waiters[id]
        del self._waiters[id]

        return data

    async def _write(self, type: RconPacketType, data: str) -> int:
        await self._lock.acquire()

        out_payload = (
            struct.pack("<ii", 0, type.value) + data.encode("utf-8") + b"\x00\x00"
        )
        self._transport.write(struct.pack("<i", len(out_payload)) + out_payload)

        await asyncio.sleep(0.003)
        self._lock.release()

    def connection_made(self, transport):
        self.state = ConnectState.CONNECTED
        self._transport = transport

    def data_received(self, data):
        data = data[4:]  # data size(4 bytes), but data_received give all data received

        (packet_id,) = struct.unpack("<i", data[:4])  # ID Field (4 bytes)
        (packet_type,) = struct.unpack("<i", data[4:8])  # Type Field (4 bytes)

        # -1 is for 1 bytes Empty string terminator
        packet_payload = data[8:-1].decode("utf-8")  # Pocket body (At least 1 byte)

        print("packet_id", packet_id, packet_type, packet_payload)
        if wait := self._waiters.get(None if packet_type == 2 else packet_id):
            wait.set_result(
                RconPacketData(
                    id=packet_id,
                    type=packet_type,
                    data=packet_payload,
                )
            )

    def connection_lost(self, exc):
        print("The server closed the connection")

    async def authenticate(self, password: str) -> None:
        self.password = password
        await self._write(RconPacketType.LOGIN, password)

        res = await self._wait_receive()
        if res["type"] == 2 and res["id"] == 0:
            self.state = ConnectState.AUTHENTICATED
            return

        raise LoginError()

    async def execute(self, command: str) -> RconPacketData:
        self._id += 1
        await self._write(RconPacketType.COMMAND_EXECUTE, command)
        return await asyncio.wait_for(
            self._wait_receive(self._id),
            timeout=self.timeout,
        )

    def close(self):
        self._transport.close()
        self.state = ConnectState.CLOSED


class RconClient:
    def __init__(
        self,
        host: str,
        port: int,
        password: str | None = None,
        loop: AbstractEventLoop | None = None,
        protocol: Protocol | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password or ""
        self.loop = asyncio.get_running_loop() if loop is None else loop
        self.protocol = RconClientProtocol(self.loop) if protocol is None else protocol

    async def connect(self) -> None:
        await self.loop.create_connection(self.protocol, "127.0.0.1", 25575)
        await self.protocol.authenticate(self.password)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    def disconnect(self) -> None:
        self.protocol.close()

    async def __aexit__(self, type, value, trace):
        self.disconnect()

    def execute(self, command: str):
        return self.protocol.execute(command)


if __name__ == "__main__":

    async def main():
        with RconClient("127.0.0.1", 25575, "1234") as client:
            await client.execute("list")

    asyncio.run(main())
