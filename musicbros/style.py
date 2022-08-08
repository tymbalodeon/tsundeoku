from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.theme import Theme

THEME_CONFIG = str(Path.home() / ".config/musicbros/theme.ini")


class PrintLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


DEFAULT_THEME = Theme(
    {
        PrintLevel.INFO.value: "dim cyan",
        PrintLevel.WARNING.value: "yellow",
        PrintLevel.ERROR.value: "bold red",
    }
)

try:
    THEME = Theme.read(THEME_CONFIG)
except Exception:
    THEME = DEFAULT_THEME


def print_with_color(text: str | int, style=PrintLevel.WARNING):
    if isinstance(text, int):
        text = f"{text:,}"
    console = Console(theme=THEME)
    console.print(text, style=style.value)
