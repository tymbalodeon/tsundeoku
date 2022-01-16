from typer import colors, secho, style

BRACKET_YEAR_REGEX = r"\s\[\d{4}\]"
BRACKET_DISC_REGEX = r"\s\[(d|D)is(c|k)\s\d+\]"
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
