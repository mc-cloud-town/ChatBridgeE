import json
from abc import ABC
from typing import Any, Optional, Self, get_type_hints

__all__ = ("Config",)


class Config(ABC):
    def __init__(self, **kwargs: Any) -> None:
        cls = self.__class__
        attrs = []

        for name, type in get_type_hints(cls).items():
            if name.startswith("_"):
                continue

            attrs.append(name)

            try:
                getattr(cls, name)
            except AttributeError:
                if name not in kwargs:
                    raise TypeError(f"Missing argument: {name}")
                if not isinstance(kwargs.get(name), type):
                    raise TypeError(f"Invalid type for argument {name}: {type}")

                setattr(self, name, kwargs.pop(name))

        self._attrs = attrs
        cls.__slots__ = attrs

        if kwargs:
            raise TypeError(f"Unexpected arguments: {','.join(kwargs.keys())}")

    def __iter__(self):
        for key in self._attrs:
            yield key, self.get(key)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Optional[None] = None) -> Optional[Any]:
        try:
            return self[key]
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> Self:
        if key not in self._attrs:
            raise AttributeError(f"Unknown attribute: {key}")
        setattr(self, key, value)
        return self

    def json(self) -> str:
        return json.dumps(self, default=lambda _: dict(self))
