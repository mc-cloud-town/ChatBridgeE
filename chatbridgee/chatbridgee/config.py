from mcdreforged.api.all import Serializable


class NoMissingFieldSerializable(Serializable):
    @classmethod
    def deserialize(cls, data: dict, **kwargs):
        kwargs.setdefault("error_at_missing", True)
        return super().deserialize(data, **kwargs)

    @classmethod
    def get_default(cls):
        return cls.deserialize({}, error_at_missing=False)


class ClientInfo(NoMissingFieldSerializable):
    name: str
    password: str


class ChatBridgeEConfig(Serializable):
    # 連線名稱
    name: str = "Survival"
    # 連線密碼
    password: str = "SurvivalPassword"
    # 伺服器位址
    server_hostname: str = "127.0.0.1"
    # 伺服器連接埠
    server_port: int = 8081
    # 省略特定玩家發送的訊息
    chat_blacklist_names: list[str] = ["REC_PCRC"]

    # -----------------------------------------
    # --------------- file sync ---------------
    # -----------------------------------------
    # 啟用檔案同步
    file_sync_enabled: bool = False
    # 檔案同步路徑
    file_sync_path: str = "world/config/worldedit/schematic/*"
    # 檔案同步副檔名
    file_sync_extension: str = ".schem"
    # 檔案同步指令前綴
    file_sync_command_prefix: str = "!!sch"

    @property
    def client_info(self) -> ClientInfo:
        return ClientInfo(name=self.name, password=self.password)

    @property
    def server_address(self) -> str:
        return f"{self.server_hostname}:{self.server_port}"
