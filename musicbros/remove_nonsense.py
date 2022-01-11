from re import escape, sub
from subprocess import run

from beets.ui import _configure, _open_library
from typer import echo


def list_items(
    query_tag,
    query,
    operate_on_albums,
    lib=_open_library(_configure({})),
):
    query_string = f"'{query_tag}::{query}'"
    items = lib.albums(query_string) if operate_on_albums else lib.items(query_string)
    albums = [item.get(query_tag) for item in items]
    return albums


def get_album_operation_flag(operate_on_albums):
    return "-a" if operate_on_albums else ""


def beet_modify(confirm, operate_on_albums, modify_tag, found, replacement):
    run(
        [
            "beet",
            "modify",
            "" if confirm else "-y",
            get_album_operation_flag(operate_on_albums),
            f"{modify_tag}::^{found}$",
            f"{modify_tag}={replacement}",
        ]
    )


def update_tag(find_regex, replacement, tags, confirm, operate_on_albums, modify_tag):
    tags = [(escape(tag), sub(find_regex, replacement, tag)) for tag in tags]
    for found_value, replacement_value in tags:
        beet_modify(
            confirm, operate_on_albums, modify_tag, found_value, replacement_value
        )


def update_tags(
    query_regex,
    query_tag,
    modify_tag,
    find_regex,
    replacement,
    operate_on_albums,
    confirm,
):
    tags = list_items(query_tag, query_regex, operate_on_albums)
    update_tag(
        find_regex, replacement, tags, confirm, operate_on_albums, modify_tag
    ) if tags else echo("No albums to update.")


def strip_bracket_years():
    echo('Removing bracketed years from all "album" tags...')
    update_tags(
        query_regex=r"\s\[\d{4}\]",
        query_tag="album",
        modify_tag="album",
        find_regex=r"\s\[\d{4}\]",
        replacement="",
        operate_on_albums=True,
        confirm=False,
    )


def replace_recs_with_recordings():
    echo('Replacing "Rec.s" with "Recordings" in all "album" tags...')
    update_tags(
        query_regex=r"\bRec\.s\b",
        query_tag="album",
        modify_tag="album",
        find_regex=r"\bRec\.s\b",
        replacement="Recordings",
        operate_on_albums=True,
        confirm=False,
    )


def strip_bracket_solo_instruments():
    echo('Removing "solo" instrument brackets from all "artist" tags...')
    update_tags(
        query_regex=r"\s\[solo.+\]",
        query_tag="album",
        modify_tag="album",
        find_regex=r"\s\[solo.+\]",
        replacement="",
        operate_on_albums=True,
        confirm=False,
    )


def remove_nonsense_main():
    strip_bracket_years()
    replace_recs_with_recordings()
    strip_bracket_solo_instruments()
