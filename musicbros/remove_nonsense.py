from re import escape, sub
from subprocess import run

from typer import echo

from .helpers import BRACKET_YEAR_REGEX, LIBRARY

ACTIONS = [
    (
        'Removing bracketed years from all "album" tags...',
        BRACKET_YEAR_REGEX,
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
        'Removing "solo" instrument brackets from all "artist" tags...',
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


def beet_modify(confirm, operate_on_albums, modify_tag, found, replacement):
    run(
        [
            "beet",
            "modify",
            "" if confirm else "-y",
            "-a" if operate_on_albums else "",
            f"{modify_tag}::^{found}$",
            f"{modify_tag}={replacement}",
        ]
    )


def remove_nonsense_main():
    for action in ACTIONS:
        message, find, replace, tag, operate_on_albums = action
        echo(message)
        tags = [
            (escape(tag), sub(find, replace, tag))
            for tag in list_items(tag, find, operate_on_albums)
        ]
        if tags:
            for found_value, replacement_value in tags:
                beet_modify(
                    False, operate_on_albums, tag, found_value, replacement_value
                )
            else:
                echo("No albums to update.")
