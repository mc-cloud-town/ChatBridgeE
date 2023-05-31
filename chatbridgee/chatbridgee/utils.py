from io import BytesIO as IoBytesIO

__all__ = (
    "BytesIO",
    "FileEncode",
)


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
    | `3+n`    | `2`     | data length (m)        |
    | `5+n`    | `m`     | data                   |
    | `5+n+m`  | `2`     | server name length (o) |
    | `7+n+m`  | `o`     | server name            |
    """

    def __init__(
        self,
        path: str,
        data: bytes,
        *,
        flag: int = 0,
        server_name: str | None = None,
    ) -> None:
        self.path = path
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
            # [m] data length (2)
            + len(data_bytes := self.data).to_bytes(2, "big")
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
            flag = int.from_bytes(bio.read(1))
            path = bio.read(int.from_bytes(bio.read(2))).decode("utf-8")
            data = bio.read(int.from_bytes(bio.read(2)))
            server_name = (
                None
                if bio.end
                else bio.read(int.from_bytes(bio.read(2))).decode("utf-8")
            )

            return cls(path, data, flag=flag, server_name=server_name)
