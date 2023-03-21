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
    name: str = "ClientName"
    password: str = "ClientPassword"
    server_hostname: str = "127.0.0.1"
    server_port: int = 8081

    @property
    def client_info(self) -> ClientInfo:
        return ClientInfo(name=self.name, password=self.password)

    @property
    def server_address(self) -> str:
        return f"{self.server_hostname}:{self.server_port}"
