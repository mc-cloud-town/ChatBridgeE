import copy
from enum import EnumMeta
from functools import lru_cache
from types import NoneType, UnionType
from typing import (
    Any,
    Literal,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

__all__ = (
    "ConfigData",
    "parse_type",
)

_T = TypeVar("_T")


class ConfigData:
    def __init__(self, **kwargs: Any) -> None:
        if self._set_attr(kwargs):
            raise TypeError(f"Invalid arguments: {', '.join(kwargs.keys())}")

    @classmethod
    @lru_cache()
    def get_hint_type(cls) -> dict[str, Any]:
        return {
            name: type
            for name, type in get_type_hints(cls).items()
            if not name.startswith("_")
        }

    @classmethod
    def default(cls):
        return cls()

    def _set_attr(self, kwargs: dict[str, Any], *, copy_default: bool = True) -> None:
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}.copy()
        for name, type in self.get_hint_type().items():
            default_value = getattr(self, name)
            value = kwargs.pop(
                name,
                copy.copy(default_value) if copy_default else default_value,
            )
            setattr(self, name, parse_type(value, type))

        return kwargs


_BASIC_TYPES = (NoneType, bool, int, float, str, list, dict)


def parse_type(data: Any, cls: Type[_T]) -> _T:
    def warn_type(*expected_type: Type):
        return TypeError(
            "Mismatched input type: expected class "
            + "|".join(map(lambda x: f"{x.__name__!r}", expected_type))
            + f" (deduced from {cls.__name__!r}) but found data with class "
            f"{type(data).__name__!r}"
        )

    origin = s if (s := get_origin(cls)) else cls

    if cls is None:
        cls = NoneType

    # Any
    if cls is Any:
        return data
    # check type in _BASIC_TYPES
    elif cls in _BASIC_TYPES:
        if isinstance(data, cls):
            return data

        if cls is float and isinstance(data, int):
            return float(data)

        raise warn_type(int, float)
    # Union
    elif origin in (Union, UnionType):
        for arg in (args := get_args(cls)):
            try:
                return parse_type(data, arg)
            except (ValueError, TypeError):
                pass
        raise warn_type(*args)
    # list
    elif origin is list:
        if isinstance(data, list):
            arg, *_ = (*get_args(cls), Any)
            return list(map(lambda x: parse_type(x, arg), data))
        raise warn_type(list)
    # dict
    elif origin is dict:
        if isinstance(data, dict):
            key_type, value_type, *_ = (*get_args(cls), Any, Any)
            return {
                parse_type(k, key_type): parse_type(v, value_type)
                for k, v in data.items()
            }
        raise warn_type(dict)
    # Enum
    elif isinstance(cls, EnumMeta):
        if isinstance(data, str):
            if data in cls.__dict__:
                return cls[data]
            raise ValueError(f"Invalid enum value for {cls}")
        raise warn_type(str)
    # Literal
    elif origin is Literal:
        if data in (args := get_args(cls)):
            return data
        raise warn_type(*args)

    raise TypeError(f"Type not supported: {cls.__name__}")


class Test(ConfigData):
    A: str = "A"


s = Test(A="1")
print(s.A)
