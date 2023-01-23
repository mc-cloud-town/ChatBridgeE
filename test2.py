from enum import Enum
from typing import Optional, Literal, Union

# i - italic
# b - bold
# s - strikethrough
# u - underline
# o - obfuscated
# And colors:

# w - White (default)
# y - Yellow
# m - Magenta (light purple)
# r - Red
# c - Cyan (aqua)
# l - Lime
# t - lighT blue
# f - dark grayF (weird Flex, but ok)
# g - Gray
# d - golD
# p - PurPle
# n - browN (dark red)
# q - turQuoise (dark aqua)
# e - grEEn
# v - naVy blue
# k - blaK
# #FFAACC - arbitrary RGB color (1.16+), hex notation. Use uppercase for A-F symbols

# '^<format> <text>' - hover over tooltip text,
#   appearing when hovering with your mouse over the text below.
# '?<suggestion> - command suggestion -
# a message that will be pasted to chat when text below it is clicked.
# '!<message>' - a chat message that will be executed when the text below it is clicked.
# '@<url>' - a URL that will be opened when the text below it is clicked.
# '&<text>' - a text that will be copied to clipboard when the text below it is clicked.


class FormatMark:
    def __init__(self, mark: str, code: str, ansi_escape_code: str):
        self.mark = mark
        self.code = code
        self.ansi_escape_code = ansi_escape_code


class Formatting(Enum):
    """
    Formatting marks for Minecraft messages.
    https://minecraft.fandom.com/wiki/Formatting_codes
    """

    # TODO use Color from hex(#) #([0-9a-fA-F]{6})

    ITALIC = FormatMark("i", "o", "3m")
    STRIKETHROUGH = FormatMark("s", "m", "9m")
    UNDERLINE = FormatMark("u", "n", "4m")
    BOLD = FormatMark("b", "l", "1m")
    OBFUSCATED = FormatMark("o", "k", "8m")
    RESET = FormatMark(None, "k", "0m")

    WHITE = FormatMark("w", "f", "0;97m")
    YELLOW = FormatMark("y", "e", "0;93m")
    LIGHT_PURPLE = FormatMark("m", "d", "0;95m")
    RED = FormatMark("r", "c", "0;91m")
    AQUA = FormatMark("c", "b", "0;96m")
    GREEN = FormatMark("l", "a", "0;92m")
    BLUE = FormatMark("t", "9", "0;94m")
    DARK_GRAY = FormatMark("f", "8", "0;90m")
    GRAY = FormatMark("g", "7", "0;37m")
    GOLD = FormatMark("d", "6", "0;33m")
    DARK_PURPLE = FormatMark("p", "5", "0;35m")
    DARK_RED = FormatMark("n", "4", "0;31m")
    DARK_AQUA = FormatMark("q", "3", "0;36m")
    DARK_GREEN = FormatMark("e", "2", "0;32m")
    DARK_BLUE = FormatMark("v", "1", "0;34m")
    BLACK = FormatMark("k", "0", "0;30m")

    @classmethod
    def values(cls) -> list[FormatMark]:
        return [value for _, value in cls.items()]

    @classmethod
    def keys(cls) -> list[str]:
        return [key for key, _ in cls.items()]

    @classmethod
    def items(cls) -> list[tuple[str, FormatMark]]:
        return list(map(lambda c: (c.name, c.value), cls))


class MCMessageFormat:
    def __init__(self, *msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return f"<MCMessageFormat msg={self.msg}>"

    # def __add__(self, other):
    #     return MCMessageFormat(self.msg + other.msg)

    def _parse(self, type: Union[Literal["mc"], Literal["ansi"]] = "mc") -> str:
        return "".join([self._parse_mark(msg, type=type) for msg in self.msg])

    def _parse_mark(
        self,
        msg: str,
        type: Union[Literal["mc"], Literal["ansi"]] = "mc",
    ) -> str:
        marks, *msgs = msg.split(" ")
        style, end_style = "", ""

        for mark in marks:
            _mark = self.get_mark(mark)
            if _mark is None:
                continue

            if type == "mc":
                style += f"§{_mark.code}"
            elif type == "ansi":
                style += f"\033[{_mark.ansi_escape_code}"

        if type == "mc":
            end_style = f"§{Formatting.RESET.value.code}"
        elif type == "ansi":
            end_style = f"\033[{Formatting.RESET.value.ansi_escape_code}"

        return f"{style}{' '.join(msgs)}{end_style}"

    def get_mark(self, mark: str) -> Optional[FormatMark]:
        for value in Formatting.values():
            if value.mark == mark:
                return value

        return None
