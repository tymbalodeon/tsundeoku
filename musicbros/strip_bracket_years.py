import os
import re

dirname = os.path.dirname(__file__)
TEMP_NAME = os.path.join(dirname, "beets_tag_reformatter_temp.txt")


def get_album_flag(album):
    """generate beet flag for album level operations"""
    if album:
        return "-a"
    return ""


def get_prompt_flag(prompt):
    """generate beet flag for prompt"""
    if prompt:
        return ""
    return "-y"


def get_beets_list_command_to_file(album, query_tag, query, reformat_tag):
    """generate beet command for list"""
    album_string = get_album_flag(album)
    return (
        f"beet ls {album_string} \"{query_tag}::{query}\" -f '${reformat_tag}' >>"
        f" {TEMP_NAME}"
    )


def get_beets_list_command(album, query_tag, query, reformat_tag):
    """generate beet command for list"""
    album_string = get_album_flag(album)
    return f"beet ls {album_string} \"{query_tag}::{query}\" -f '${reformat_tag}'"


def get_beets_modify_command(prompt, album, reformat_tag, old, new):
    """generate beet command for modify"""
    prompt_string = get_prompt_flag(prompt)
    album_string = get_album_flag(album)
    return (
        f'beet modify {prompt_string} {album_string} "{reformat_tag}::^{old}$"'
        f' {reformat_tag}="{new}"'
    )


def get_items():
    """get items from temp file and format into array"""
    results_raw = open(TEMP_NAME)
    results = results_raw.read().split("\n")
    results = results[:-1]
    results_raw.close()
    return results


def rewrite_tag(find, replace, items, prompt, album, reformat_tag):
    """write new tag values"""
    for old in items:
        new = re.sub(find, replace, old)
        old_escaped = re.escape(old)
        old_escaped = old_escaped.replace("\\", "\\\\")
        old_escaped = old_escaped.replace('"', r"\"")
        old_escaped = old_escaped.replace(":", r"\:")
        modify_command_string = get_beets_modify_command(
            prompt, album, reformat_tag, old_escaped, new
        )
        os.system(modify_command_string)


def beets_reformat(query, query_tag, reformat_tag, find, replace, album, prompt):
    """reformat audio tags"""
    list_command_string = get_beets_list_command_to_file(
        album, query_tag, query, reformat_tag
    )
    os.system(list_command_string)
    results = get_items()
    if len(results) == 0:
        print("All albums formatted correctly.")
    else:
        rewrite_tag(find, replace, results, prompt, album, reformat_tag)
    os.system(f"rm {TEMP_NAME}")


def strip_bracket_years():
    beets_reformat("\s\[\d{4}\]", "album", "album", "\s\[\d{4}\]", "", True, False)
