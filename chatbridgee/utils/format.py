import re

__all__ = ("dcToMcFormatting",)


ResetText = "§r"
ResetRe = re.compile(f"({ResetText})+")

dcFormatConvert = {
    # ~~ 刪除線 §m
    "~~": {"replace": "§m", "re": re.compile(r"(?<!\\)~~([\s\S]+?)~~(?!~)")},
    # __ 底線 §n
    "__": {"replace": "§o", "re": re.compile(r"(?<!\\)__([\s\S]+?)__(?!_)")},
    # ** 粗體 §l
    "**": {"replace": "§o", "re": re.compile(r"(?<!\\)\*\*([\s\S]+?)\*\*(?!\*)")},
    # _  斜體 §o
    "_": {"replace": "§n", "re": re.compile(r"(?<!\\)_([\s\S]+?)_(?!_)")},
    # *  斜體 §o
    "*": {"replace": "§l", "re": re.compile(r"(?<!\\)\*([\s\S]+?)\*(?!\*)")},
}


def dcToMcFormatting(s: str) -> str:
    def match_replace(match: re.Match, replace: str) -> str:
        return f"{replace}{match.group(1)}{ResetText}"

    for value in dcFormatConvert.values():
        replace: str = value.get("replace")
        match: re.Pattern[str] = value.get("re")

        s = match.sub(lambda m: match_replace(m, replace), s)

    return ResetRe.sub(ResetText, s)
