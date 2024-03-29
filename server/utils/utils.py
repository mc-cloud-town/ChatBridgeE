from __future__ import annotations

from io import BytesIO as IoBytesIO
from pathlib import Path
from typing import Any

__all__ = (
    "MISSING",
    "format_number",
    "BytesIO",
    "FileEncode",
)


class _MissingSentinel:
    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


def format_number(number: int) -> str:
    suffixes = " KMGTP"
    suffix_index = 0

    while number >= 1000 and suffix_index < len(suffixes) - 1:
        number /= 1000
        suffix_index += 1

    return f"{number:.2f}".rstrip("0").rstrip(".") + suffixes[suffix_index]


class BytesIO(IoBytesIO):
    def __len__(self) -> int:
        return self.getbuffer().nbytes

    @property
    def end(self) -> bool:
        return self.size <= self.tell()

    @property
    def size(self) -> int:
        return len(self)


class FileEncode:
    """
    | `offset` | `bytes` | `description`          |
    | -------- | ------- | ---------------------- |
    | `0`      | `1`     | flag                   |
    | `1`      | `2`     | path length (n)        |
    | `3`      | `n`     | path                   |
    | `3+n`    | `4`     | data length (m)        |
    | `7+n`    | `m`     | data                   |
    | `7+n+m`  | `2`     | server name length (o) |
    | `9+n+m`  | `o`     | server name            |
    """

    def __init__(
        self,
        path: str | Path,
        data: bytes,
        *,
        flag: int = 0,
        server_name: str | None = None,
    ) -> None:
        self.path = str(path)
        self.data = data
        self.flag = flag
        self.server_name = server_name

    def encode(self) -> bytes:
        data = (
            # flag (1)
            self.flag.to_bytes(1, "big")
            # [n] path length (2)
            + len(path_bytes := self.path.encode(encoding="utf-8")).to_bytes(2, "big")
            # path (n)
            + path_bytes
            # [m] data length (4)
            + len(data_bytes := self.data).to_bytes(4, "big")
            # data (m)
            + data_bytes
        )
        if self.server_name:
            data += (
                # [o] server name length
                len(server_name_bytes := self.server_name.encode("utf-8")).to_bytes(
                    2,
                    "big",
                )
                # server name (o)
                + server_name_bytes
            )
        return data

    def __str__(self) -> str:
        return (
            f"<FileEncode path={self.path} flag={self.flag} "
            f"server_name={self.server_name}>"
        )

    __repr__ = __str__

    @classmethod
    def decode(cls, raw_data: bytes) -> "FileEncode":
        """encode to data"""
        with BytesIO(raw_data) as bio:
            flag = int.from_bytes(bio.read(1), "big")
            path = bio.read(int.from_bytes(bio.read(2), "big")).decode("utf-8")
            data = bio.read(int.from_bytes(bio.read(4), "big"))
            server_name = (
                None
                if bio.end
                else bio.read(int.from_bytes(bio.read(2), "big")).decode("utf-8")
            )

            return cls(path, data, flag=flag, server_name=server_name)
