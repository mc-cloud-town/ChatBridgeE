import json
import logging
from pathlib import Path
from typing import Any, Dict, Generic, Literal, Optional, TypeVar, NamedTuple, Union

import yaml

__all__ = ("Config", "ConfigType")


log = logging.getLogger("chat-bridgee")
_RT = TypeVar("_RT", bound=NamedTuple)
_T = TypeVar("_T")


class UserAuth(NamedTuple):
    password: str
    display_name: Optional[str]


class UserData(NamedTuple):
    name: str
    display_name: Optional[str]


class ConfigType(NamedTuple):
    stop_plugins: list[str] = "plugins"
    users: Dict[str, UserAuth] = {}  # dict[name, UserAuth]
    plugins_path: str = []


class Config(Generic[_RT]):
    def __init__(
        self,
        config_name: str,
        config_path: Union[str, Path, None] = None,
        config_type: Union[Literal["json"], Literal["yaml"]] = "json",
        default_config: Optional[_RT] = None,
    ) -> None:
        self.directory = Path(config_path or "")
        self.config_type = config_type
        self.filepath = self.directory / f"{config_name}.{config_type}"

        if default_config is None:
            self.default_config = ConfigType(
                stop_plugins=[],
                users={"Survival": UserAuth("SurvivalPassword", "生存服")._asdict()},
                plugins_path="plugins",
            )

        self.check_config()

    def check_config(self, replay: bool = False) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        filepath = self.filepath

        if not filepath.is_file() or replay:
            with filepath.open("w", encoding="UTF-8") as f:
                log.info(f"正在嘗試生成設定檔... {self.default_config}")
                data = self.default_config._asdict()

                if self.config_type == "json":
                    json.dump(data, f, ensure_ascii=False, indent=2)
                elif self.config_type == "yaml":
                    yaml.dump(data, f, allow_unicode=True, indent=2)
                log.info(f"設定檔生成完成，'./{filepath}'")

    def read_config(self) -> dict:
        try:
            with self.filepath.open("r", encoding="UTF-8") as f:
                if self.config_type == "json":
                    data = json.load(f)
                elif self.config_type == "yaml":
                    data = yaml.load(f, Loader=yaml.FullLoader)
                    if type(data) not in (dict,):  # base type is dict, not list or else
                        raise json.JSONDecodeError("", "", 0)
        except (json.JSONDecodeError, yaml.constructor.ConstructorError):
            log.warn("無效的設定檔，正在嘗試生成...")
            self.check_config(replay=True)
            return self.read_config()

        return dict(**data)

    def write(self, data: _RT) -> None:
        self.check_config()

        with self.filepath.open("w", encoding="UTF-8") as f:
            if self.config_type == "json":
                json.dump(data, f, ensure_ascii=False)
            elif self.config_type == "yaml":
                yaml.dump(data, f, allow_unicode=True)

    def get(self, key: str, default: Optional[_T] = None) -> _T:
        return self.read_config().get(
            key,
            default or self.default_config._field_defaults.get(key),
        )

    def set(self, key: str, value: Any) -> None:
        data = self.read_config()
        data.update({key: value})
        self.write(data)

    def append(self, key: str, value: Any, *, only_one: bool = False) -> None:
        if (data := self.get(key)) is not None and type(data) is not list:
            return None

        if only_one and value in data:
            return None

        self.set(key, [*(data or []), value])

    def remove(self, key: str, value: Any) -> None:
        if type(self.get(key)) is not list:
            return None

        try:
            data = self.get(key, [])
            data.remove(value)
        except ValueError:
            pass
        else:
            self.set(key, data)
