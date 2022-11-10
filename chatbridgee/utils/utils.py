import json
from typing import Any


__all__ = ("MISSING", "ClassJson")


class _MissingSentinel:
    def __eq__(self, _) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


class ClassJson:
    def __init__(self, **kwargs) -> None:
        self.__kwargs = kwargs

    def __repr__(self) -> str:
        return json.dumps(self.__kwargs)

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key: str):
        return self.__kwargs.get(key, None)
