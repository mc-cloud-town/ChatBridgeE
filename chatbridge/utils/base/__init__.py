from typing import NamedTuple
from .cryptor import *


class Address(NamedTuple):
    hostname: str
    port: int

    def __str__(self):
        return f"{self.hostname}:{self.port}"
