import copy
import logging
from enum import EnumMeta
from functools import lru_cache
from types import NoneType, UnionType
from typing import (
    Any,
    ClassVar,
    Literal,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

__all__ = (
    "Data",
    "parse_type",
)

_T = TypeVar("_T")
_BASIC_TYPES = (NoneType, bool, int, float, str, list, dict, set, tuple)
DataType = TypeVar("DataType", bound="Data")
log = logging.getLogger("typehint")


class TypeHintError(TypeError):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)


def parse_type(data: Any, cls: Type[_T]) -> _T:
    def warn_type(*expected_type: Type):
        return TypeHintError(
            "Mismatched input type: expected class "
            + "|".join(map(lambda x: f"{x.__name__!r}", expected_type))
            + f" (deduced from {cls.__name__!r}) but found data with class "
            f"{type(data).__name__!r}"
        )

    origin = get_origin(cls) or cls

    if cls is None:
        cls = NoneType

    # Any
    if cls is Any:
        return data
    # check type in _BASIC_TYPES
    elif cls in _BASIC_TYPES:
        if isinstance(data, cls):
            return data

        # int -> float
        if cls is float:
            if isinstance(data, int):
                return float(data)
            raise warn_type(float, int)
        # [list|tuple] -> set
        if cls is set and isinstance(data, (list, tuple)):
            log.warning(
                f"The target type is set, but the provided {type(data).__name__!r} "
                "is automatically converted. However, the type definition is "
                "different, and it is recommended to use set directly."
            )
            return set(data)
        # [list|set] -> set
        if cls is tuple and isinstance(data, (list, set)):
            return tuple(data)
        # [set|tuple] -> list
        if cls is list and isinstance(data, (tuple, set)):
            return list(data)

        raise warn_type(cls)
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
    # TypeVar
    elif isinstance(origin, TypeVar):
        for arg in (args := origin.__constraints__ or (Any,)):
            try:
                return parse_type(data, arg)
            except (ValueError, TypeError):
                pass
        raise warn_type(*args)
    # Literal
    elif origin is Literal:
        if data in (args := get_args(cls)):
            return data
        raise warn_type(*args)

    raise TypeError(f"Type not supported: {cls.__name__}")


class DataMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, Any], **kwargs):
        attrs["__annotations__"].update(cls.__annotations__)
        attrs["__annotations__"].update(
            {
                k: type(v)
                for k, v in attrs.items()
                if not k.startswith("_")
                and not callable(v)
                and not isinstance(v, (classmethod, staticmethod, property))
            }
        )
        annotations: dict = attrs["__annotations__"]
        attrs["__comments__"] = {
            k[1:]: str(v)
            for k, v in attrs.items()
            if k.startswith("_") and not k.startswith("__") and k[1:] in annotations
        }
        required_keys = set()
        for k in annotations.keys():
            try:
                attrs[k]
            except KeyError:
                required_keys.add(k)
        attrs["__required_keys__"] = required_keys
        attrs["__optional_keys__"] = set(
            k for k in annotations.keys() if k not in required_keys
        )

        return super().__new__(cls, name, bases, attrs, **kwargs)


class Data(metaclass=DataMeta):
    __comments__: ClassVar[dict[str, str]]
    __required_keys__: ClassVar[set[str]]
    __optional_keys__: ClassVar[set[str]]

    def __init__(self, **kwargs: Any) -> None:
        for required in self.__required_keys__:
            if required not in kwargs:
                raise ValueError(f"Missing required argument: {required}")
        if tmp := self._set_attr(kwargs):
            raise ValueError(f"Invalid arguments: {', '.join(tmp.keys())}")

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

    def _set_attr(
        self,
        kwargs: dict[str, Any],
        *,
        copy_default: bool = True,
        default: Any = ...,
    ) -> dict[str, Any]:
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("_")}.copy()
        for name, type in self.get_hint_type().items():
            default_value = getattr(self, name, default)
            value = kwargs.pop(
                name,
                copy.copy(default_value) if copy_default else default_value,
            )
            setattr(self, name, parse_type(value, type))

        return kwargs

    def merge(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._set_attr(data)

    def dump(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.get_hint_type()}

    def get(self, key: str, default: _T = None) -> Any | _T:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> _T:
        return self.get(key)

    def __str__(self) -> str:
        arg = " ".join(f"{k}={v}" for k, v in self.dump().items())
        return f"<{self.__class__.__name__} {arg}".strip() + ">"

    __repr__ = __str__
