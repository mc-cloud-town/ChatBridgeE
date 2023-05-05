"""
https://developer.valvesoftware.com/wiki/Source_RCON_Protocol
"""

import asyncio
from asyncio import AbstractEventLoop, BaseTransport, Future, Lock
from enum import Enum, auto
import struct
from typing import Self


class RconPacketType(Enum):
    COMMAND_RESPONSE = 0
    COMMAND_EXECUTE = 2
    LOGIN = 3


class ConnectState(Enum):
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATED = auto()


class RconClientProtocol(asyncio.Protocol):
    def __init__(self, password: str, loop: AbstractEventLoop | None = None):
        self.password = password
        self.state = ConnectState.CONNECTING

        self._id = -1
        self._buffer = b""
        self._transport: BaseTransport | None = None
        self._loop = asyncio.get_running_loop() if loop is None else loop
        self._waiters = dict[str, Future]()
        self._lock = Lock()

    def __call__(self) -> Self:
        return self

    async def _wait_receive(self, id: int = None):
        self._waiters[id] = self._loop.create_future()

        await self._waiters[id]
        del self._waiters[id]

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
        # print(packet_type)
        # print(packet_payload)

        if wait := self._waiters.get(None if packet_type == 2 else packet_id):
            wait.set_result(packet_payload)

    def connection_lost(self, exc):
        print("The server closed the connection")

    async def authenticate(self) -> None:
        await self._write(RconPacketType.LOGIN, self.password)
        res = await self._wait_receive()
        print(res)

    async def execute(self, command: str) -> None:
        self._id += 1
        await self._write(RconPacketType.COMMAND_EXECUTE, command)
        res = await asyncio.wait_for(self._wait_receive(self._id), timeout=10)
        print(res)


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    protocol = RconClientProtocol("1234")

    await loop.create_connection(protocol, "127.0.0.1", 25575)
    await protocol.authenticate()
    await protocol.execute("list")


asyncio.run(main())
