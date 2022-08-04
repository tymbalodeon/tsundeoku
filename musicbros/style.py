from enum import Enum

from typer import colors


class Color(Enum):
    BLUE = colors.BLUE
    CYAN = colors.CYAN
    GREEN = colors.GREEN
    MAGENTA = colors.MAGENTA
    RED = colors.RED
    YELLOW = colors.YELLOW
    WHITE = colors.WHITE


def color(text: str, color=Color.YELLOW, bold=False) -> str:
    text = f"{text:,}" if isinstance(text, int) else str(text)
    style = color.value
    if bold:
        style = f"bold {style}"
    return f"[{style}]{text}[/{style}]"
