from typer import colors, secho, style

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
    if isinstance(text, int):
        text = f"{text:,}"
    return secho(text, fg=COLORS[color]) if echo else style(text, fg=COLORS[color])
