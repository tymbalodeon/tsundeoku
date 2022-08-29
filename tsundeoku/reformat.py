from dataclasses import dataclass
from re import escape, sub

from beets.library import Library
from rich import print

from .library import get_library, modify_tracks
from .regex import (
    BRACKET_YEAR_REGEX,
    ORIGINAL_REGEX,
    RECORDING_REGEX,
    RECORDINGS_REGEX,
    SOLO_INSTRUMENT_REGEX,
)


@dataclass
class Action:
    message: str
    find: str
    replace: str
    tag: str = "album"
    operate_on_albums: bool = True


ACTIONS = [
    Action(
        message='Removing bracketed years from all "album" tags...',
        find=BRACKET_YEAR_REGEX,
        replace="",
    ),
    Action(
        message='Replacing "Rec." with "Recording" in all "album" tags...',
        find=RECORDING_REGEX,
        replace="Recording",
    ),
    Action(
        message='Replacing "Recs" with "Recordings" in all "album" tags...',
        find=RECORDINGS_REGEX,
        replace="Recordings",
    ),
    Action(
        message='Replacing "Orig." with "Original" in all "album" tags...',
        find=ORIGINAL_REGEX,
        replace="Original",
    ),
    Action(
        message=(
            'Removing bracketed solo instrument indications from all "artist" tags...'
        ),
        find=SOLO_INSTRUMENT_REGEX,
        replace="",
        tag="artist",
        operate_on_albums=False,
    ),
]


def list_items(
    query_tag: str,
    query: str,
    operate_on_albums: bool,
    library: Library | None = None,
) -> list[str]:
    if not library:
        library = get_library()
    query_string = f"'{query_tag}::{query}'"
    if operate_on_albums:
        albums_or_items = library.albums(query_string)
    else:
        albums_or_items = library.items(query_string)
    return [album_or_item.get(query_tag) for album_or_item in albums_or_items]


def reformat(action: Action):
    if action.message:
        print(action.message)
    items = list_items(action.tag, action.find, action.operate_on_albums)
    tags = [(escape(tag), sub(action.find, action.replace, tag)) for tag in items]
    if not tags:
        print("No albums to update.")
        return
    for found_value, replacement_value in tags:
        query = [
            f"{action.tag}::^{found_value}$",
            f"{action.tag}={replacement_value}",
        ]
        modify_tracks(query, action.operate_on_albums, False)


def reformat_main(solo_instruments=False):
    actions = ACTIONS if solo_instruments else ACTIONS[:-1]
    for action in actions:
        reformat(action)
