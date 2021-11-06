from os import path, remove, system
from pathlib import Path
from re import escape, sub

from typer import echo

dirname = path.dirname(__file__)
TEMP_FILE = Path(dirname) / ".beets_tag_reformatter_temp"


def get_album_operation_flag(operate_on_albums):
    return "-a" if operate_on_albums else ""


def beet_ls(operate_on_albums, query_tag, query, update_tag):
    system(
        f"beet ls {get_album_operation_flag(operate_on_albums)}"
        f" \"{query_tag}::{query}\" -f '${update_tag}' >> {TEMP_FILE}"
    )
    with open(TEMP_FILE) as tags:
        tags = tags.read().split("\n")[:-1]
    remove(TEMP_FILE)
    return tags


def beet_modify(confirm, operate_on_albums, tag, old, new):
    return (
        "beet"
        f" modify{' ' if confirm else ' -y '}"
        f'{get_album_operation_flag(operate_on_albums)} "{tag}::^{old}$"'
        f' {tag}="{new}"'
    )


def update_tag(find, replace, tags, confirm, operate_on_albums, tag):
    for tag in tags:
        updated_tag = sub(find, replace, tag)
        escaped_tag = (
            escape(tag).replace("\\", "\\\\").replace('"', r"\"").replace(":", r"\:")
        )
        system(beet_modify(confirm, operate_on_albums, tag, escaped_tag, updated_tag))


def update_album_tags(
    query, query_tag, update_tag, find, replace, operate_on_albums, confirm
):
    tags = beet_ls(operate_on_albums, query_tag, query, update_tag)
    update_tag(
        find, replace, tags, confirm, operate_on_albums, update_tag
    ) if tags else echo("All albums formatted correctly.")


def strip_bracket_years():
    echo("Removing bracketed years from album fields...")
    update_album_tags(
        query=r"\s\[\d{4}\]",
        query_tag="album",
        update_tag="album",
        find=r"\s\[\d{4}\]",
        replace="",
        operate_on_albums=True,
        confirm=False,
    )
