from enum import Enum
from typing import Optional


class ChatFormatting(Enum):
    OBFUSCATED = ("k", "o")
    BOLD = ("l", "b")
    STRIKETHROUGH = ("m", "s")
    UNDERLINE = ("n", "u")
    ITALIC = ("o", "i")
    RESET = ("r")

    BLACK = ("0", "k", 0x000000)
    DARK_BLUE = ("1", "v", 0x0000AA)
    DARK_GREEN = ("2", "e", 0x00AA00)
    DARK_AQUA = ("3", "q", 0x00AAAA)
    DARK_RED = ("4", "n", 0xAA0000)
    DARK_PURPLE = ("5", "p", 0xAA00AA)
    GOLD = ("6", "d", 0xFFAA00)
    GRAY = ("7", "g", 0xAAAAAA)
    DARK_GRAY = ("8", "f", 0x555555)
    BLUE = ("9", "t", 0x5555FF)
    GREEN = ("a", "l", 0x55FF55)
    AQUA = ("b", "c", 0x55FFFF)
    RED = ("c", "r", 0xFF5555)
    LIGHT_PURPLE = ("d", "m", 0xFF55FF)
    YELLOW = ("e", "y", 0xFFFF55)
    WHITE = ("f", "w", 0xFFFFFF)

    def __init__(
        self,
        code: str,
        mark: Optional[str] = None,
        integer: Optional[int] = None,
    ):
        self.code = code
        self.mark = mark
        self.color = -1 if integer is None else integer
        self.is_format = integer is None

    def __str__(self):
        return f"\u00a7{self.code}"  # f"§{self.code}"

    def __repr__(self):
        return f"<ChatFormatting name={self.name} mark={self.mark}>"


class MCMessenger:
    def get_chat_component_form_text(self, msg: str) -> dict:
        if msg.startswith(" "):
            msg = f"w{msg}"

        desc, *texts = msg.split(" ")
        text = " ".join(texts)

    def parse_style(
        self,
    ):
        ...


print(ChatFormatting.OBFUSCATED.is_format)
print(ChatFormatting.OBFUSCATED.color)
