"""
https://developer.valvesoftware.com/wiki/Source_RCON_Protocol
"""

import asyncio
import logging
import struct
from asyncio import AbstractEventLoop, BaseTransport, Future, Lock, Protocol
from enum import Enum, auto
from typing import Self, TypedDict

log = logging.getLogger("chat-bridgee")


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

        self._transport: BaseTransport | None = None
        self._loop = asyncio.get_running_loop() if loop is None else loop
        self._wait_read = Future[RconPacketData]()
        self._lock = Lock()
        self.timeout = command_timeout

    def __call__(self) -> Self:
        return self

    def connection_made(self, transport):
        self.state = ConnectState.CONNECTED
        self._transport = transport

    def data_received(self, data):
        # [data size(4 bytes), but data_received give all data received]:4
        data = data[4:]

        # [ID Field (4 bytes), Type Field (4 bytes)]:8
        (packet_id, packet_type) = struct.unpack("<ii", data[:8])

        if data[-2:] != b"\x00\x00":
            log.error("Incorrect padding")
        if packet_id == -1:
            log.error("Login failed")

        # -1 is for 1 bytes Empty string terminator
        # Pocket body (At least 1 byte)
        packet_payload = data[8:-2].decode("utf-8")

        log.debug(f"read id: {packet_id};type: {packet_type};data: {packet_payload}")
        self._wait_read.set_result(
            RconPacketData(
                id=packet_id,
                type=packet_type,
                data=packet_payload,
            )
        )

    def connection_lost(self, exc):
        log.info(f"[{self._transport}] The server closed the connection")

    def close(self):
        self._transport.close()
        self.state = ConnectState.CLOSED

    def is_connected(self) -> bool:
        return self.state in {ConnectState.CONNECTED, ConnectState.AUTHENTICATED}

    async def _send(self, type: RconPacketType, data: str) -> RconPacketData:
        await self._lock.acquire()

        out_payload = (
            struct.pack("<ii", 0, type.value) + data.encode("utf-8") + b"\x00\x00"
        )
        self._transport.write(struct.pack("<i", len(out_payload)) + out_payload)

        data = await self._wait_read
        self._wait_read = Future[RconPacketData]()
        self._lock.release()
        return data

    async def authenticate(self, password: str) -> None:
        self.password = password
        res = await self._send(RconPacketType.LOGIN, password)
        if res["type"] == 2 and res["id"] == 0:
            self.state = ConnectState.AUTHENTICATED
            return

        raise LoginError()

    async def execute(
        self,
        command: str,
        *,
        timeout: float | None = None,
    ) -> RconPacketData:
        return await asyncio.wait_for(
            self._send(RconPacketType.COMMAND_EXECUTE, command),
            timeout=self.timeout if timeout is None else timeout,
        )


class RconClient:
    def __init__(
        self,
        host: str | None = None,
        port: int | str | None = None,
        password: str | None = None,
        loop: AbstractEventLoop | None = None,
        protocol: Protocol | None = None,
    ) -> None:
        self.host = "localhost" if host is None else host
        self.port = int(25575 if port is None else port)
        self.password = "" if password is None else password
        self.loop = asyncio.get_running_loop() if loop is None else loop
        self.protocol = RconClientProtocol(self.loop) if protocol is None else protocol

    @property
    def is_connected(self):
        return self.protocol.is_connected()

    async def connect(self, *, exception: bool = False) -> None:
        if self.is_connected:
            if exception:
                raise Exception("Connection is already established")
            return

        await self.loop.create_connection(self.protocol, self.host, self.port)
        await self.protocol.authenticate(self.password)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    def disconnect(self) -> None:
        self.protocol.close()

    async def __aexit__(self, type, value, trace):
        self.disconnect()

    def execute(self, command: str, *, timeout: float | None = None):
        return self.protocol.execute(command, timeout=timeout)


if __name__ == "__main__":

    async def main():
        async with RconClient("127.0.0.1", 25575, "1234") as client:
            result = await client.execute("list")
            print(result["data"])

    asyncio.run(main())
