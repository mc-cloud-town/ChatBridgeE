from typing import Any


class _MissingSentinel:
    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


def format_number(number: int) -> str:
    suffixes = " KMGTP"
    suffix_index = 0

    while number >= 1000 and suffix_index < len(suffixes) - 1:
        number /= 1000
        suffix_index += 1

    return f"{number:.2f}".rstrip("0").rstrip(".") + suffixes[suffix_index]
