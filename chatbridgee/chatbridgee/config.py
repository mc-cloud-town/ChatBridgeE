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
    name: str = "Survival"
    password: str = "SurvivalPassword"
    server_hostname: str = "127.0.0.1"
    server_port: int = 8081
    chat_blacklist_names: list[str] = ["REC_PCRC"]

    @property
    def client_info(self) -> ClientInfo:
        return ClientInfo(name=self.name, password=self.password)

    @property
    def server_address(self) -> str:
        return f"{self.server_hostname}:{self.server_port}"
