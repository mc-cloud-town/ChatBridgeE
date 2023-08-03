from __future__ import annotations

import json
from abc import ABC
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional, TypeVar, Union

import yaml

__all__ = ("Config",)

_T = TypeVar("_T")


class Config(ABC):
    __config_filetype__: ClassVar[Union[Literal["json"], Literal["yaml"]]]
    __config_path__: ClassVar[Union[str, Path]]
    __config_name__: ClassVar[str]

    def __init__(self, **kwargs: Any) -> None:
        cls = self.__class__
        self._attrs = []

        self.__config_file_path__ = kwargs.pop(
            "_config_path",
            Path(cls.__config_path__)
            / f"{cls.__config_name__}.{cls.__config_filetype__}",
        )
        self._kwargs = kwargs

        self.reload()

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
        self.reload()
        return getattr(self, key)

    def get(self, key: str, default: Optional[None] = None) -> Optional[_T]:
        try:
            return self[key]
        except AttributeError:
            return default

    def set(self, key: str, value: Any) -> None:
        if key not in self._attrs:
            raise AttributeError(f"Unknown attribute: {key}")
        setattr(self, key, value)

    def json(self) -> Union[list, dict]:
        return json.loads(self.json_str())

    def json_str(self) -> str:
        return json.dumps(self, default=lambda _: dict(self))

    def yaml_str(self) -> str:
        return yaml.dump(self.json(), allow_unicode=True)

    @classmethod
    def load(
        cls,
        _filetype: Optional[Union[Literal["json"], Literal["yaml"]]] = "yaml",
        _config_path: Optional[Union[str, Path]] = None,
        _name: Optional[str] = None,
        _auto_create: bool = False,
        **kwargs: Any,
    ) -> "Config":
        _config_path = _config_path or cls.__config_path__
        file_type = _filetype or cls.__config_filetype__
        path = Path(_config_path) / f"{_name or cls.__config_name__}.{file_type}"

        if data := cls.load_data(path, file_type):
            return cls(**data, _config_path=path)

        new_data = cls(**kwargs, _config_path=path)
        if _auto_create:
            new_data.save()
        return new_data

    @classmethod
    def load_data(cls, path: Path | str, file_type: str) -> dict | None:
        if (path := Path(path)).is_file():
            with open(path, "r", encoding="utf-8") as f:
                if file_type == "json":
                    return json.load(f)
                else:
                    file_type = "yaml"
                    return yaml.load(f, Loader=yaml.FullLoader)
        else:
            return None

    def reload(self) -> None:
        self._attrs = []
        self._kwargs = self.load_data(
            self.__config_file_path__,
            self.__config_filetype__,
        )

        for name, value in self.__class__.__dict__.items():
            if name.startswith("_"):
                continue

            self._attrs.append(name)
            value = self._kwargs.pop(name, value) if self._kwargs else value
            setattr(self, name, value)

    def save(
        self,
        filetype: Optional[Union[Literal["json"], Literal["yaml"]]] = None,
        config_path: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
    ) -> None:
        config_type = filetype or self.__config_filetype__
        path = (
            Path(config_path or self.__config_path__)
            / f"{name or self.__config_name__}.{config_type}"
        )

        if not (parent := path.parent).is_dir():
            parent.mkdir(parents=True)

        with open(path, "w", encoding="utf-8") as f:
            if config_type == "json":
                json.dump(self, f, default=lambda _: dict(self))
            else:
                yaml.dump(self.json(), f, allow_unicode=True, indent=2)
