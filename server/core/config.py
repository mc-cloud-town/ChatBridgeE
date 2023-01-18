import json
import logging
from pathlib import Path
from typing import Literal, Optional, TypedDict, TypeVar, Union

import yaml

__all__ = ("Config", "ConfigType")

P = TypeVar("P")

log = logging.getLogger("chat-bridgee")


class Config:
    def __init__(
        self,
        config_name: str,
        config_path: Union[str, Path, None] = None,
        config_type: Union[Literal["json"], Literal["yaml"]] = "json",
    ) -> None:
        self.directory = Path(config_path or "")
        self.config_type = config_type
        self.filepath = self.directory / f"{config_name}.{config_type}"

        self.check_config()

    def check_config(self, replay: bool = False) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        filepath = self.filepath

        if not filepath.is_file() or replay:
            with filepath.open("w", encoding="UTF-8") as f:
                log.info("正在嘗試生成設定檔...", self.default_config)
                if self.config_type == "json":
                    json.dump(self.default_config, f, ensure_ascii=False, indent=2)
                elif self.config_type == "yaml":
                    yaml.dump(self.default_config, f, allow_unicode=False, indent=2)
                log.info(f"設定檔生成完成，'./{filepath}'")

    def read_config(self) -> "ConfigType":
        try:
            with self.filepath.open("r", encoding="UTF-8") as f:
                if self.config_type == "json":
                    data = json.load(f)
                elif self.config_type == "yaml":
                    data = yaml.load(f, Loader=yaml.FullLoader)
                    if type(data) not in (dict,):  # base type is dict, not list or else
                        raise json.JSONDecodeError("", "", 0)
        except json.JSONDecodeError:
            log.warn("無效的設定檔，正在嘗試生成...")
            self.check_config(replay=True)
            return self.read_config()

        return ConfigType(**data)

    # TODO use dict key, value type
    def get(self, key: P, default: Optional[P] = None):
        return self.read_config().get(key, default)

    @classmethod
    @property
    def default_config(self) -> "ConfigType":
        return ConfigType(
            stop_plugins=[],
        )


class ConfigType(TypedDict):
    stop_plugins: list[str]  # 關閉的插劍
