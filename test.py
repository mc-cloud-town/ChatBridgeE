# while True:
#     try:
#         print(next(t))
#     except StopIteration:
#         break


from typing import Optional


def dcToMcFormatting(s: str) -> str:
    legal = ["*", "_", "~"]
    maxLen: int = len(s) - 1

    result = ""
    check: bool = False

    asteriskItalic = False  # * 斜體 §o
    underlineItalic = False  # _ 斜體 §o
    asteriskBold = False  # **  粗體 §l
    underlineBold = False  # __  底線 §n
    strikeThrough = False  # ~~  刪除線 §m

    def checkReset() -> str:
        if (
            asteriskItalic
            and asteriskBold
            and underlineItalic
            and underlineBold
            and strikeThrough
        ):
            return ""
        return "§r"

    index = 0

    while index <= maxLen:
        no = s[index]
        ne: Optional[str] = s[index + 1] if maxLen > index else None  # next
        index += 1

        if no == "\\":
            index += 1
            result += ne or ""
            continue

        if no == "*" and ne == "*":  # - '**'
            index += 1
            result += "§l"
            continue
        if no == "_" and ne == "_":  # - '__'
            index += 1
            result += "§n"
            continue
        if no == "~" and ne == "~":  # - '~~'
            index += 1
            result += "§m"
            continue
        if no == "_" or no == "*":  # - '_' or '*'
            result += "§o"
            continue

        result += no

    return result


print(dcToMcFormatting("0123456**awa"))
