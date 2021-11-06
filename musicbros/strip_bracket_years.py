from os import path, remove, system
from pathlib import Path
from re import escape, sub

dirname = path.dirname(__file__)
TEMP_NAME = Path(dirname) / "beets_tag_reformatter_temp.txt"


def get_album_flag(album):
    return "-a" if album else ""


def get_prompt_flag(prompt):
    return "" if prompt else "-y"


def get_beets_list_command(album, query_tag, query, reformat_tag, to_file=False):
    to_file_command = f" >> {TEMP_NAME}"
    return (
        f"beet ls {get_album_flag(album)} \"{query_tag}::{query}\" -f '${reformat_tag}'"
        f"{to_file_command if to_file else ''}"
    )


def get_beets_modify_command(prompt, album, reformat_tag, old, new):
    return (
        f"beet modify {get_prompt_flag(prompt)} {get_album_flag(album)}"
        f' "{reformat_tag}::^{old}$" {reformat_tag}="{new}"'
    )


def get_items():
    with open(TEMP_NAME) as raw_results:
        return raw_results.read().split("\n")[:-1]


def rewrite_tag(find, replace, tracks, prompt, album, reformat_tag):
    for old_tag in tracks:
        new_tag = sub(find, replace, old_tag)
        old_escaped = (
            escape(old_tag)
            .replace("\\", "\\\\")
            .replace('"', r"\"")
            .replace(":", r"\:")
        )
        system(
            get_beets_modify_command(prompt, album, reformat_tag, old_escaped, new_tag)
        )


def beets_reformat(query, query_tag, reformat_tag, find, replace, album, prompt):
    system(get_beets_list_command(album, query_tag, query, reformat_tag))
    results = get_items()
    if not len(results):
        print("All albums formatted correctly.")
    else:
        rewrite_tag(find, replace, results, prompt, album, reformat_tag)
    remove(TEMP_NAME)


def strip_bracket_years():
    print("Removing bracketed years from album fields...")
    beets_reformat("\s\[\d{4}\]", "album", "album", "\s\[\d{4}\]", "", True, False)
