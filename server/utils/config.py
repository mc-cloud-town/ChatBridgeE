import json
from abc import ABC
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional, Union, get_type_hints

import yaml
from typeguard import check_type

__all__ = ("Config",)


class Config(ABC):
    __config_filetype__: ClassVar[Union[Literal["json"], Literal["yaml"]]]
    __config_path__: ClassVar[Union[str, Path]]
    __config_name__: ClassVar[str]

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
                    try:
                        check_type(name, None, type)
                    except TypeError:
                        raise TypeError(f"Missing argument: {name}")
                    setattr(self, name, None)
                    continue
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

    def set(self, key: str, value: Any) -> None:
        if key not in self._attrs:
            raise AttributeError(f"Unknown attribute: {key}")
        setattr(self, key, value)

    def json(self) -> Union[list, dict]:
        return json.loads(self.json_str())

    def json_str(self) -> str:
        return json.dumps(self, default=lambda _: dict(self))

    def yaml_str(self) -> str:
        return yaml.dump(self.json())

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

        if path.is_file():
            with open(path, "r") as f:
                if file_type == "json":
                    return cls(**json.load(f))
                return cls(**yaml.load(f, Loader=yaml.FullLoader))

        new_data = cls(**kwargs)
        if _auto_create:
            new_data.save()
        return new_data

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

        with open(path, "w") as f:
            if config_type == "json":
                json.dump(self, f, default=lambda _: dict(self))
            else:
                yaml.dump(self.json(), f)
