from enum import Enum

from beets import config
from beets.ui import _configure, _open_library, decargs
from beets.ui.commands import modify_items, modify_parse_args
from typer import colors, echo, style

LIBRARY = _open_library(_configure({"verbose": 0, "replace": dict(), "timeout": 5}))


def modify_tracks(args: list, album: bool, confirm: bool, library=LIBRARY):
    query, modifications, deletions = modify_parse_args(decargs(args))
    if not modifications and not deletions:
        echo("ERROR: No modifications specified.")
        return
    try:
        config_import = config["import"]
        write = config_import["write"]
        move = config_import["move"]
        copy = config_import["copy"]
        move = move.get(bool) or copy.get(bool)
        modify_items(
            library,
            modifications,
            deletions,
            query,
            write.get(bool),
            move,
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
