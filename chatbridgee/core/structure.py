from typing import List, TypedDict

from chatbridgee.utils.utils import ClassJson


class PayloadStructure(TypedDict):
    sender: str
    data: dict
    receivers: List[str]


class PayloadSender(ClassJson):
    pass
