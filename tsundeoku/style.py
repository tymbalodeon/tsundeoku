from enum import Enum

from rich.console import Console
from rich.syntax import Syntax
from rich.theme import Theme


class StyleLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


THEME = Theme(
    {
        StyleLevel.INFO.value: "dim cyan",
        StyleLevel.WARNING.value: "yellow",
        StyleLevel.ERROR.value: "bold red",
    }
)


def print_with_theme(text: Syntax | str, level: StyleLevel | None = None):
    console = Console(theme=THEME)
    if level:
        style = THEME.styles[level.value]
        console.print(text, style=style)
    else:
        console.print(text)


def wrap_in_style(text: str, style: str) -> str:
    opening_tag = f"[{style}]"
    if "link" in style:
        link_tag = style.split("=")[0]
        closing_tag = f"[/{link_tag}]"
    else:
        closing_tag = f"[/{style}]"
    return f"{opening_tag}{text}{closing_tag}"


def stylize(text: str, styles: list[str] | str) -> str:
    if isinstance(styles, str):
        return wrap_in_style(text, styles)
    else:
        for style in styles:
            text = wrap_in_style(text, style)
    return text


def stylize_path(path: str) -> str:
    path = f'"{path}"'
    return stylize(path, "green")
