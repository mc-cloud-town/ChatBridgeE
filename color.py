from enum import Enum

MC_COLOR_TOKEN = "\u00a7"  # "§"


class Color(Enum):
    # https://minecraft.fandom.com/wiki/Formatting_codes
    # https://minecraft.fandom.com/wiki/Raw_JSON_text_format
    BLACK = ("0", 0x000000, "30")
    DARK_BLUE = ("1", 0x0000AA, "34")
    DARK_GREEN = ("2", 0x00AA00, "32")
    DARK_AQUA = ("3", 0x00AAAA, "36")
    DARK_RED = ("4", 0xAA0000, "31")
    DARK_PURPLE = ("5", 0xAA00AA, "35")
    GOLD = ("6", 0xFFAA00, "33")
    GRAY = ("7", 0xAAAAAA, "37")
    DARK_GRAY = ("8", 0x555555, "90")
    BLUE = ("9", 0x5555FF, "94")
    GREEN = ("a", 0x55FF55, "92")
    AQUA = ("b", 0x55FFFF, "96")
    RED = ("c", 0xFF5555, "91")
    LIGHT_PURPLE = ("d", 0xFF55FF, "95")
    YELLOW = ("e", 0xFFFF55, "93")
    WHITE = ("f", 0xFFFFFF, "97")

    OBFUSCATED = ("k", None, "1-9-3")
    BOLD = ("l", None, "1")
    STRIKETHROUGH = ("m", None, "9")
    UNDERLINE = ("n", None, "4")
    ITALIC = ("o", None, "3")
    RESET = ("r", None, "0")

    def __init__(
        self,
        mark: str,
        integer: int | None = None,
        ansi: str | None = None,
    ):
        self.mark = mark
        self.id = self._name_.lower()
        self.is_format = integer is None
        self.is_color = not self.is_format
        self.color = -1 if integer is None else integer

        self.base_ansi = ansi.split("-") if ansi else []

    @property
    def ansi(self) -> str:
        return f"\033[{';'.join(self.base_ansi)}m" if self.base_ansi else ""

    def __str__(self):
        return f"{MC_COLOR_TOKEN}{self.mark}"

    def __repr__(self):
        return (
            f"<{self._name_} name={self.ansi}{self._name_.lower()}\033[0m "
            f"mc={str(self)}>"
        )

    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def formats(cls):
        return [f for f in cls if f.is_format]

    @classmethod
    def colors(cls):
        return [f for f in cls if not f.is_format]

    @classmethod
    def from_mark(cls, mark: str, default: "Color" = WHITE):
        return next((f for f in cls if f.mark == mark), default)


def parse(text: str):
    catch, offset = dict[str, int](), 0
    result, catch_data = list[dict | str]([""]), dict[str, dict]()
    command_catch_text = ""

    text_len = len(text)
    while offset < text_len:
        char, next_char = (
            text[offset],
            text[offset + 1] if offset < text_len - 1 else None,
        )
        offset += 1

        if char == "\\":
            offset += 1

        if char == "[":
            catch["["] = offset
        elif char == "]" and catch.get("["):
            catch["]"] = offset
        elif char == "(" and catch.get("]") == offset - 1:
            catch["("] = offset
        elif char == ")" and (t3 := catch.pop("(", None)):
            t1, t2, t4 = catch.pop("["), catch.pop("]"), offset
            name, arg = text[t1 : t2 - 1], text[t3 : t4 - 1]

            result.append(catch_data)
            tmp = dict(catch_data.copy(), text=name, clickEvent={})
            result.append(tmp)
            continue
        elif char == "*":
            ...
        elif char == "_":
            ...
        elif char == "~" and next_char == "~":
            offset += 1
            if old_pos := catch.pop("~~", None):
                result.append(catch_data)

                catch_data["text"] = text[old_pos : offset - 2]
                catch_data["strikethrough"] = True
                continue
            catch["~~"] = offset
        elif char == "|":
            ...
        elif char == "#":
            if next_char == "r":
                result.append(catch_data)
                catch_data = {}
                continue
            catch_data["color"] = Color.from_mark(next_char).id
            offset += 1
            continue

        data = catch_data.get("text", "") + char
        if catch.get("["):
            command_catch_text = data
        else:
            catch_data["text"] = data

    if catch.get("["):
        catch_data["text"] = command_catch_text

    return result


# [111](command:say 1)~~test~~
print(parse("#eawa[111](command:say1)"))
# import time

# s = []
# for i in range(99):
#     start = time.perf_counter()
#     for _ in range(100000):
#         parse("awa [run command](command:)")
#     end = time.perf_counter()
#     print(f"{i+1:02d}. {(t := end - start):.12f}")
#     s.append(t)
# print(f"--- {min(s):.12f}")
# print(f"--- {sum(s):.12f}")


"[run command](command:)"  # run command
"[go web](https?:)"  # open url
"[copy to clipboard](copy:)"  # copy to clipboard
"[suggest command](suggest:)"  # suggest command
"[show text](show_text:)"  # show text

"**bold**"  # bold
"*italic*"  # italic
"__underline__"  # underlined
"_strikethrough_"  # strikethrough
"~~strikethrough~~"  # strikethrough
"||(-)+||"  # obfuscated
"#0"  # BLACK
"#1"  # DARK_BLUE
"#2"  # DARK_GREEN
"#3"  # DARK_AQUA
"#4"  # DARK_RED
"#5"  # DARK_PURPLE
"#6"  # GOLD
"#7"  # GRAY
"#8"  # DARK_GRAY
"#9"  # BLUE
"#a"  # GREEN
"#b"  # AQUA
"#c"  # RED
"#d"  # LIGHT_PURPLE
"#e"  # YELLOW
"#f"  # WHITE

# print("\n".join(map(repr, Color.all())))
