from re import escape, sub
from subprocess import PIPE, run

from typer import echo


def get_album_operation_flag(operate_on_albums):
    return "-a" if operate_on_albums else ""


def beet_ls(operate_on_albums, query_tag, query, format_tag):
    tags = (
        run(
            [
                "beet",
                "ls",
                operate_on_albums,
                f'"{query_tag}::{query}"',
                "-f",
                f"'${format_tag}'",
            ],
            stdout=PIPE,
        )
        .stdout.decode("utf-8")
        .split("\n")
    )
    tags = [tag for tag in tags if tag]
    return tags


def beet_modify(confirm, operate_on_albums, modify_tag, found, replacement):
    run(
        [
            "beet",
            "modify",
            "" if confirm else "-y",
            operate_on_albums,
            f'"{modify_tag}::^{found}$"',
            f'{modify_tag}="{replacement}"',
        ]
    )


def update_tag(find_regex, replacement, tags, confirm, operate_on_albums, modify_tag):
    tags = [(escape(tag), sub(find_regex, replacement, tag)) for tag in tags]
    for found_value, replacement_value in tags:
        beet_modify(
            confirm, operate_on_albums, modify_tag, found_value, replacement_value
        )


def update_album_tags(
    query_regex,
    query_tag,
    modify_tag,
    find_regex,
    replacement,
    operate_on_albums,
    confirm,
):
    operate_on_albums = get_album_operation_flag(operate_on_albums)
    tags = beet_ls(operate_on_albums, query_tag, query_regex, modify_tag)
    update_tag(
        find_regex, replacement, tags, confirm, operate_on_albums, modify_tag
    ) if tags else echo("No albums to update.")


def strip_bracket_years():
    echo('Removing bracketed years from all albums\' "album" tag...')
    update_album_tags(
        query_regex=r"\s\[\d{4}\]",
        query_tag="album",
        modify_tag="album",
        find_regex=r"\s\[\d{4}\]",
        replacement="",
        operate_on_albums=True,
        confirm=False,
    )
