from enum import Enum
from pathlib import Path

from beets import config
from beets.ui import _configure, _open_library, decargs
from beets.ui.commands import modify_items, modify_parse_args
from typer import colors, echo, style

LIBRARY = _open_library(_configure({"verbose": 0, "replace": dict(), "timeout": 5}))
BRACKET_YEAR_REGEX = r"\s\[\d{4}\]"
BRACKET_DISC_REGEX = r"\s\[(d|D)is(c|k)\s\d+\]"
BRACKET_SOLO_INSTRUMENT = r"\s\[solo\s[a-z]+\]"


def create_directory(new_directory: Path, parents=True) -> Path:
    if not new_directory.exists():
        Path.mkdir(new_directory, parents=parents)
    return new_directory


def modify_tracks(args: list, album: bool, confirm: bool, library=LIBRARY):
    query, modifications, deletions = modify_parse_args(decargs(args))
    if not modifications and not deletions:
        echo("ERROR: No modifications specified.")
        return
    try:
        modify_items(
            library,
            modifications,
            deletions,
            query,
            config["import"]["write"].get(bool),
            config["import"]["move"].get(bool) or config["import"]["copy"].get(bool),
            album,
            confirm,
        )
    except Exception:
        echo("No matching albums found.")


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
    return style(text, fg=color.value, bold=bold)
