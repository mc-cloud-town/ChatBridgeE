import json
from abc import ABC
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional, Self, Union, get_type_hints

import yaml
from typeguard import check_type

__all__ = ("Config",)


class Config(ABC):
    __config_filetype__: ClassVar[Union[Literal["json"], Literal["yaml"]]]
    __config_path__: ClassVar[Union[str, Path]]
    __config_name__: ClassVar[str]

    def __init__(self, *args, **kwargs: Any) -> None:
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
                try:
                    check_type(name, kwargs.get(name), type)
                except TypeError:
                    raise TypeError(f"Invalid type for argument {name}: {type}")
                setattr(self, name, kwargs.pop(name))

        self._attrs = attrs
        cls.__slots__ = attrs

        if kwargs:
            raise TypeError(f"Unexpected arguments: {','.join(kwargs.keys())}")

    def __init_subclass__(
        cls,
        type: Union[Literal["json"], Literal["yaml"]] = "yaml",
        path: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init_subclass__()

        cls.__config_filetype__ = type
        cls.__config_path__ = path or Path() / "config"
        cls.__config_name__ = name or cls.__name__

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

    def json(self) -> Union[list, dict]:
        return json.loads(self.json_str())

    def json_str(self) -> str:
        return json.dumps(self, default=lambda _: dict(self))

    def yaml_str(self) -> str:
        return yaml.dump(self.json())
