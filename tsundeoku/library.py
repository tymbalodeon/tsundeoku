from re import escape

from beets import config
from beets.library import Library
from beets.ui import _configure, _open_library, decargs
from beets.ui.commands import modify_items, modify_parse_args
from rich import print


def get_library() -> Library:
    library_config = {"verbose": 0, "replace": {}, "timeout": 5}
    return _open_library(_configure(library_config))


def get_library_tracks(
    artist: str, album: str, library: Library | None = None
) -> list:
    if not library:
        library = get_library()
    artist = escape(artist)
    album = escape(album)
    artist_query = f"'artist::^{artist}$'"
    album_query = f"'album::^{album}$'"
    query = f"{artist_query} {album_query}"
    tracks = list(library.items(query))
    return tracks


def modify_tracks(
    args: list, album=True, confirm=False, library: Library | None = None
):
    if not library:
        library = get_library()
    query, modifications, deletions = modify_parse_args(decargs(args))
    if not modifications and not deletions:
        print("ERROR: No modifications specified.")
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
        print("No matching albums found.")
