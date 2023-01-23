"""
i - italic
b - bold
s - strikethrough
u - underline
o - obfuscated

w - White (default)
y - Yellow
m - Magenta (light purple)
r - Red
c - Cyan (aqua)
l - Lime
t - lighT blue
f - dark grayF (weird Flex, but ok)
g - Gray
d - golD
p - PurPle
n - browN (dark red)
q - turQuoise (dark aqua)
e - grEEn
v - naVy blue
k - blaK

'^<format> <text>' - hover over tooltip text,
  appearing when hovering with your mouse over the text below.
'?<suggestion> - command suggestion -
a message that will be pasted to chat when text below it is clicked.
'!<message>' - a chat message that will be executed when the text below it is clicked.
'@<url>' - a URL that will be opened when the text below it is clicked.
'&<text>' - a text that will be copied to clipboard when the text below it is clicked.

reference:
https://github.com/gnembon/fabric-carpet/blob/master/docs/scarpet/Full.md#formatcomponents--formatcomponents-
"""

from enum import Enum
import json
from typing import Any, Literal, Optional, Union, overload

# TODO use Color from hex(#) #([0-9a-fA-F]{6})
# #FFAACC - arbitrary RGB color (1.16+), hex notation. Use uppercase for A-F symbols


class FormatMark:
    def __init__(
        self,
        mark: str,
        code: str,
        ansi_escape_code: str,
        **kwargs: Any,
    ) -> None:
        self.mark = mark
        self.code = code
        self.ansi_escape_code = ansi_escape_code
        self.kwargs = kwargs

    def mc_text_struct(self, **kwargs: Any) -> dict:
        return {**self.kwargs, **kwargs}


class Formatting(Enum):
    """
    Formatting marks for Minecraft messages.
    https://minecraft.fandom.com/wiki/Formatting_codes
    https://github.com/gnembon/fabric-carpet/blob/master/docs/scarpet/Full.md#formatcomponents--formatcomponents-
    """

    ITALIC = FormatMark("i", "o", "3m", italic=True)
    STRIKETHROUGH = FormatMark("s", "m", "9m", strikethrough=True)
    UNDERLINED = FormatMark("u", "n", "4m", underlined=True)
    BOLD = FormatMark("b", "l", "1m", bold=True)
    OBFUSCATED = FormatMark("o", "k", "8m", obfuscated=True)
    RESET = FormatMark(None, "k", "0m", color="reset")

    WHITE = FormatMark("w", "f", "0;97m", color="white")
    YELLOW = FormatMark("y", "e", "0;93m", color="yellow")
    LIGHT_PURPLE = FormatMark("m", "d", "0;95m", color="light_purple")
    RED = FormatMark("r", "c", "0;91m", color="red")
    AQUA = FormatMark("c", "b", "0;96m", color="aqua")
    GREEN = FormatMark("l", "a", "0;92m", color="green")
    BLUE = FormatMark("t", "9", "0;94m", color="blue")
    DARK_GRAY = FormatMark("f", "8", "0;90m", color="dark_gray")
    GRAY = FormatMark("g", "7", "0;37m", color="gray")
    GOLD = FormatMark("d", "6", "0;33m", color="gold")
    DARK_PURPLE = FormatMark("p", "5", "0;35m", color="dark_purple")
    DARK_RED = FormatMark("n", "4", "0;31m", color="dark_red")
    DARK_AQUA = FormatMark("q", "3", "0;36m", color="dark_aqua")
    DARK_GREEN = FormatMark("e", "2", "0;32m", color="dark_green")
    DARK_BLUE = FormatMark("v", "1", "0;34m", color="dark_blue")
    BLACK = FormatMark("k", "0", "0;30m", color="black")

    @classmethod
    def values(cls) -> list[FormatMark]:
        return [value for _, value in cls.items()]

    @classmethod
    def keys(cls) -> list[str]:
        return [key for key, _ in cls.items()]

    @classmethod
    def items(cls) -> list[tuple[str, FormatMark]]:
        return list(map(lambda c: (c.name, c.value), cls))


# https://minecraft.fandom.com/wiki/Raw_JSON_text_format


class MCMessageFormat:
    def __init__(self, *msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return f"<MCMessageFormat msg={self.msg}>"

    # fmt: off
    @overload
    def parse(self, type: Literal["mc"]) -> list[dict]: ... # noqa
    @overload
    def parse(self, type: Literal["ansi"]) -> str: ... # noqa
    # fmt: on

    def parse(self, type: Union[Literal["mc"], Literal["ansi"]] = "mc") -> str:
        result = [self._parse_mark(msg, type=type) for msg in self.msg]

        if type == "mc":
            return result
        elif type == "ansi":
            return "".join(result)

    def json_str(self) -> str:
        return json.dump(self.parse("mc"))

    # fmt: off
    @overload
    def _parse_mark(self, msg: str, type: Literal["mc"]) -> dict: ... # noqa
    @overload
    def _parse_mark(self, msg: str, type: Literal["ansi"]) -> str: ... # noqa
    # fmt: on

    def _parse_mark(
        self,
        msg: str,
        type: str = "mc",
    ) -> Union[dict, str]:
        marks, *msgs = msg.split(" ")
        _msg = " ".join(msgs)
        _marks: list[FormatMark] = []

        for mark in marks:
            _mark = self.get_mark(mark)
            if _mark is None:
                continue
            _marks.append(_mark)

        if type == "ansi":
            style = "".join([f"\033[{mark.ansi_escape_code}" for mark in _marks])

            return f"{style}{_msg}\033[{Formatting.RESET.value.ansi_escape_code}"
        elif type == "mc":
            result = {"text": _msg}

            for mark in _marks:
                result.update(mark.mc_text_struct())

            return result

        return msg

    def get_mark(self, mark: str) -> Optional[FormatMark]:
        for value in Formatting.values():
            if value.mark == mark:
                return value

        return None
