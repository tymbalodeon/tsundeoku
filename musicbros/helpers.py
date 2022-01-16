from beets import config
from beets.ui import UserError, _configure, _open_library, decargs
from beets.ui.commands import modify_items, modify_parse_args
from typer import colors, secho, style

LIBRARY = _open_library(_configure({}))
BRACKET_YEAR_REGEX = r"\s\[\d{4}\]"
BRACKET_DISC_REGEX = r"\s\[(d|D)is(c|k)\s\d+\]"


def modify_tracks(args, album, confirm, library=LIBRARY):
    query, modifications, deletions = modify_parse_args(decargs(args))
    if not modifications and not deletions:
        raise UserError("no modifications specified")
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


COLORS = {
    "blue": colors.BLUE,
    "cyan": colors.CYAN,
    "green": colors.GREEN,
    "magenta": colors.MAGENTA,
    "red": colors.RED,
    "yellow": colors.YELLOW,
    "white": colors.WHITE,
}


def color(text, color="yellow", echo=False):
    text = f"{text:,}" if isinstance(text, int) else str(text)
    return secho(text, fg=COLORS[color]) if echo else style(text, fg=COLORS[color])
