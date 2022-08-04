from typing import NamedTuple


class Address(NamedTuple):
    hostname: str
    port: int

    def __str__(self):
        return f"{self.hostname}:{self.port}"
