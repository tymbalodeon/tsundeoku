from beets.library import Album, Item
from beets.ui import _configure, _open_library, input_select_objects, print_
from beets.ui.commands import _do_query, print_and_modify
from typer import colors, secho, style

LIBRARY = _open_library(_configure({}))
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


def modify_items(library, modifications, deletions, query, write, move, album, confirm):
    album_or_item_type = Album if album else Item
    for key, value in modifications.items():
        modifications[key] = album_or_item_type._parse(key, value)
    items, albums = _do_query(library, query, album, False)
    albums_or_items = albums if album else items
    print_(f"Modifying {len(albums_or_items)} {'album' if album else 'item'}s.")
    changed = []
    for album_or_item in albums_or_items:
        if (
            print_and_modify(album_or_item, modifications, deletions)
            and album_or_item not in changed
        ):
            changed.append(album_or_item)
    if not changed:
        print_("No changes to make.")
        return
    if confirm:
        if write and move:
            extra = ", move, and write tags"
        elif write:
            extra = " and write tags"
        elif move:
            extra = " and move"
        else:
            extra = ""
        changed = input_select_objects(
            f"Really modify{extra}",
            changed,
            lambda album_or_item: print_and_modify(
                album_or_item, modifications, deletions
            ),
        )
    with library.transaction():
        for album_or_item in changed:
            album_or_item.try_sync(write, move)
