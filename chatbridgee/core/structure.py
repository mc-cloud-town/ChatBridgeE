from typing import List, TypedDict


class PayloadStructure(TypedDict):
    sender: str
    data: "PayloadSender"
    receivers: List[str]


class PayloadSender(TypedDict):
    ...


class ChatEventStructure(PayloadSender):
    time: str
    player: str
    content: str
