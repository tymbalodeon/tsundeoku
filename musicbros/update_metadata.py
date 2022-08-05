from dataclasses import dataclass
from re import escape, sub

from rich import print

from .library import LIBRARY, modify_tracks
from .regex import BRACKET_YEAR_REGEX


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
        message='Replacing "Rec.s" with "Recordings" in all "album" tags...',
        find=r"\bRec\.s",
        replace="Recordings",
    ),
    Action(
        message="",
        find=r"\bRec\.s\s",
        replace="Recordings ",
    ),
    Action(
        message='Replacing "Rec." with "Recording" in all "album" tags...',
        find=r"\bRec\.s?",
        replace="Recording",
    ),
    Action(
        message="",
        find=r"\bRec\.s?\s",
        replace="Recording ",
    ),
    Action(
        message='Replacing "Orig." with "Original" in all "album" tags...',
        find=r"\bOrig\.\s",
        replace="Original ",
    ),
    Action(
        message=(
            'Removing bracketed solo instrument indications from all "artist" tags...'
        ),
        find=r"\s\[solo.+\]",
        replace="",
        tag="artist",
        operate_on_albums=False,
    ),
]


def list_items(
    query_tag: str,
    query: str,
    operate_on_albums: bool,
    library=LIBRARY,
) -> list[str]:
    query_string = f"'{query_tag}::{query}'"
    if operate_on_albums:
        albums_or_items = library.albums(query_string)
    else:
        albums_or_items = library.items(query_string)
    return [album_or_item.get(query_tag) for album_or_item in albums_or_items]


def update_metadata(action: Action):
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


def update_metadata_main(solo_instruments=False):
    actions = ACTIONS if solo_instruments else ACTIONS[:-1]
    for action in actions:
        update_metadata(action)


def update_metadata_if_as_is(imports: bool, as_is: bool):
    if imports and not as_is:
        update_metadata_main()
