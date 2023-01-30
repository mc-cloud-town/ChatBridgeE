"""
Minecraft Chat Formatting
=========================
This module provides a way to parse Minecraft chat formatting and colors.
It also provides a way to convert Minecraft chat formatting and colors to
ANSI escape sequences.

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

^<format> <text> - hover over tooltip text, appearing when hovering with your mouse
    over the text below.
?<suggestion>    - command suggestion - a message that will be pasted to chat when text
    below it is clicked.
!<message>       - a chat message that will be executed when the text below
    it is clicked.
@<url>           - a URL that will be opened when the text below it is clicked.
&<text>          - a text that will be copied to clipboard when the text below
    it is clicked.

reference:
https://github.com/gnembon/fabric-carpet/blob/master/docs/scarpet/Full.md#formatcomponents--formatcomponents-
"""
from enum import Enum
from typing import Optional


class ChatFormatting(Enum):
    # https://minecraft.fandom.com/wiki/Raw_JSON_text_format
    OBFUSCATED = ("k", "o", None, "8")
    BOLD = ("l", "b", None, "8")
    STRIKETHROUGH = ("m", "s", None, "8")
    UNDERLINE = ("n", "u", None, "8")
    ITALIC = ("o", "i", None, "8")

    BLACK = ("0", "k", 0x000000, "0-30")
    DARK_BLUE = ("1", "v", 0x0000AA, "0-34")
    DARK_GREEN = ("2", "e", 0x00AA00, "0-32")
    DARK_AQUA = ("3", "q", 0x00AAAA, "0-36")
    DARK_RED = ("4", "n", 0xAA0000, "0-31")
    DARK_PURPLE = ("5", "p", 0xAA00AA, "0-35")
    GOLD = ("6", "d", 0xFFAA00, "0-33")
    GRAY = ("7", "g", 0xAAAAAA, "0-37")
    DARK_GRAY = ("8", "f", 0x555555, "0-90")
    BLUE = ("9", "t", 0x5555FF, "0-94")
    GREEN = ("a", "l", 0x55FF55, "0-92")
    AQUA = ("b", "c", 0x55FFFF, "0-96")
    RED = ("c", "r", 0xFF5555, "0-91")
    LIGHT_PURPLE = ("d", "m", 0xFF55FF, "0-95")
    YELLOW = ("e", "y", 0xFFFF55, "0-93")
    WHITE = ("f", "w", 0xFFFFFF, "0-97")

    def __init__(
        self,
        code: str,
        mark: Optional[str] = None,
        integer: Optional[int] = None,
        ansi: Optional[str] = None,
    ):
        self.code = code
        self.mark = mark
        self.color = -1 if integer is None else integer
        self.is_format = integer is None
        self.is_color = not self.is_format

        self.ansi = f"\033[{';'.join(ansi.split('-'))}m" if ansi else ""

    def __str__(self):
        return f"\u00a7{self.code}"  # f"§{self.code}"

    def __repr__(self):
        return f"<ChatFormatting name={self.name} mark={self.mark}>"

    @classmethod
    def formats(cls):
        return [f for f in cls if f.is_format]

    @classmethod
    def colors(cls):
        return [f for f in cls if not f.is_format]


def split_desc_text(msg: str) -> tuple[str, str]:
    if msg.startswith(" "):
        msg = f"w{msg}"

    desc, *texts = msg.split(" ")
    return desc, " ".join(texts)


def get_chat_component_form_text(msg: str) -> dict:
    desc, text = split_desc_text(msg)
    style = {"text": text}

    for mark, event in {
        "?": {"clickEvent": {"action": "suggest_command"}},
        "!": {"clickEvent": {"action": "run_command"}},
        "^": {"hoverEvent": {"action": "show_text"}},
        "@": {"clickEvent": {"action": "open_url"}},
        "&": {"clickEvent": {"action": "copy_to_clipboard"}},
    }.items():
        if desc.startswith(mark):
            desc = desc[1:]

            event[list(event.keys())[0]]["value"] = text if mark == "^" else desc[1:]
            style.update(event)

            if mark == "^":
                return style
            break

    return {**style, **parse_style(desc)[0]}


def get_ansi_console(msg: str) -> tuple[dict, str]:
    if msg.startswith(" "):
        msg = f"w{msg}"

    desc, *texts = msg.split(" ")
    text = " ".join(texts)

    return f"{parse_style(desc)[1]}{text}\033[0m"


def chat_format(*msgs: str):
    ansi = ""
    mc = []

    for msg in msgs:
        ansi += get_ansi_console(msg)
        mc.append(get_chat_component_form_text(msg))

    return {"mc": mc, "ansi": ansi, "base": "".join(msgs)}


def parse_style(desc: str) -> tuple[dict, str]:
    style = {}
    ansi_str = ""

    for format in ChatFormatting.formats():
        if format.mark in desc:
            style.update({format.name.lower(): True})
            ansi_str += format.ansi

    for color in ChatFormatting.colors():
        if color.mark in desc:
            style.update({"color": color.name.lower()})
            ansi_str += color.ansi
            break

    return style, ansi_str
