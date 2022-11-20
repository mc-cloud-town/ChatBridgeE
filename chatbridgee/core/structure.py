from typing import List, TypedDict


class PayloadStructure(TypedDict):
    event_name: str
    data: "PayloadSender"
    receivers: List[str]


class PayloadSender(TypedDict):
    ...


class ChatEventStructure(PayloadSender):
    """聊天事件"""

    time: str
    player: str
    content: str


class PlayerJoinedEventStructure(PayloadSender):
    """玩家加入事件"""

    player_name: str


class PlayerLeftEventStructure(PayloadSender):
    """玩家離開事件"""

    player_name: str


EventStructures = {
    "server_start": -1,
    "server_startup": -1,
    "server_stop": -1,
    "chat": ChatEventStructure,
    "player_joined": PlayerJoinedEventStructure,
    "player_left": PlayerLeftEventStructure,
}
