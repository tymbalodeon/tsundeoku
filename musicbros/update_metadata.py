from dataclasses import dataclass
from re import escape, sub

from typer import echo

from .helpers import BRACKET_YEAR_REGEX, LIBRARY, modify_tracks


@dataclass
class Action:
    message: str
    find: str
    replace: str
    tag: str
    operate_on_albums: bool


ACTIONS = [
    Action(
        'Removing bracketed years from all "album" tags...',
        BRACKET_YEAR_REGEX,
        "",
        "album",
        True,
    ),
    Action(
        'Replacing "Rec.s" with "Recordings" in all "album" tags...',
        r"\bRec\.s",
        "Recordings",
        "album",
        True,
    ),
    Action(
        "",
        r"\bRec\.s\s",
        "Recordings ",
        "album",
        True,
    ),
    Action(
        'Replacing "Rec." with "Recording" in all "album" tags...',
        r"\bRec\.s?",
        "Recording",
        "album",
        True,
    ),
    Action(
        "",
        r"\bRec\.s?\s",
        "Recording ",
        "album",
        True,
    ),
    Action(
        'Replacing "Orig." with "Original" in all "album" tags...',
        r"\bOrig\.\s",
        "Original ",
        "album",
        True,
    ),
    Action(
        'Removing bracketed solo instrument indications from all "artist" tags...',
        r"\s\[solo.+\]",
        "",
        "artist",
        False,
    ),
]


def list_items(
    query_tag: str,
    query: str,
    operate_on_albums: bool,
    library=LIBRARY,
) -> list[str]:
    query_string = f"'{query_tag}::{query}'"
    albums_or_items = (
        library.albums(query_string)
        if operate_on_albums
        else library.items(query_string)
    )
    return [album_or_item.get(query_tag) for album_or_item in albums_or_items]


def update_metadata(action: Action):
    if action.message:
        echo(action.message)
    items = list_items(action.tag, action.find, action.operate_on_albums)
    tags = [(escape(tag), sub(action.find, action.replace, tag)) for tag in items]
    if not tags:
        echo("No albums to update.")
        return
    for found_value, replacement_value in tags:
        query = [
            f"{action.tag}::^{found_value}$",
            f"{action.tag}={replacement_value}",
        ]
        modify_tracks(query, action.operate_on_albums, False)


def update_metadata_main(solo_instruments=False):
    actions = ACTIONS if solo_instruments else ACTIONS[:-1]
    for action in actions:
        update_metadata(action)


def update_metadata_if_as_is(imports: bool, as_is: bool):
    if imports and not as_is:
        update_metadata_main()
