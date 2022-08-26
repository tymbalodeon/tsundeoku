from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.theme import Theme


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


def format_int_with_commas(number: int) -> str:
    return f"{number:,}"


def get_theme_config() -> str:
    home = Path.home()
    config_path = home / ".config/tsundeoku"
    theme_config = config_path / "theme.ini"
    return str(theme_config)


def get_theme() -> Theme:
    try:
        theme_config = get_theme_config()
        return Theme.read(theme_config)
    except Exception:
        return DEFAULT_THEME


def print_with_color(text: str | int, style=PrintLevel.WARNING):
    theme = get_theme()
    console = Console(theme=theme)
    console.print(text, style=style.value)
