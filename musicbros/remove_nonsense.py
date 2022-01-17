from re import escape, sub

from typer import echo

from .helpers import BRACKET_DISC_REGEX, BRACKET_YEAR_REGEX, LIBRARY, modify_tracks

ACTIONS = [
    (
        'Removing bracketed years from all "album" tags...',
        BRACKET_YEAR_REGEX,
        "",
        "album",
        True,
    ),
    (
        'Removing bracketed discs from all "album" tags...',
        BRACKET_DISC_REGEX,
        "",
        "album",
        True,
    ),
    (
        'Replacing "Rec.s" with "Recordings" in all "album" tags...',
        r"\bRec\.s\b",
        "Recordings",
        "album",
        True,
    ),
    (
        'Removing bracketed solo instrument indications from all "artist" tags...',
        r"\s\[solo.+\]",
        "",
        "artist",
        False,
    ),
]


def list_items(
    query_tag,
    query,
    operate_on_albums,
    library=LIBRARY,
):
    query_string = f"'{query_tag}::{query}'"
    albums_or_items = (
        library.albums(query_string)
        if operate_on_albums
        else library.items(query_string)
    )
    return [album_or_item.get(query_tag) for album_or_item in albums_or_items]


def remove_nonsense(action):
    message, find, replace, tag, operate_on_albums = action
    echo(message)
    tags = [
        (escape(tag), sub(find, replace, tag))
        for tag in list_items(tag, find, operate_on_albums)
    ]
    if tags:
        for found_value, replacement_value in tags:
            query = [
                f"{tag}::^{found_value}$",
                f"{tag}={replacement_value}",
            ]
            modify_tracks(query, operate_on_albums, False)
        else:
            echo("No albums to update.")


def remove_nonsense_main():
    for action in ACTIONS:
        remove_nonsense(action)
