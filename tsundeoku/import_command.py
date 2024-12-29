import re
from os import listdir
from pathlib import Path
from shutil import copy
from typing import Literal

from rich import print
from rich.prompt import Confirm
from tinytag import TinyTag

from tsundeoku.config import Paths


def format_field(
    *,
    field: str,
    regex: str,
    reformat: bool,
    confirm_message: str | None,
    allow_prompt: bool,
) -> str | None:
    if not reformat:
        return field
    match = re.search(regex, field)
    if match is None:
        return field
    if not allow_prompt:
        return None
    if confirm_message:
        if not Confirm.ask(confirm_message):
            return field
    return field.replace(match.group(), "")


def get_confirm_message(*, ask: bool, message: str) -> str | None:
    if not ask:
        return None
    return message


def display_message(
    action: Literal["Error"] | Literal["Importing"], message: str
):
    if action == "Error":
        action_color = "red"
        message_color = action_color
        indent = "    "
    else:
        action_color = "green"
        message_color = "white"
        indent = ""
    print(
        f"  {indent}[{action_color} bold]{action}[/] [{message_color}]{message}[/]"
    )


def import_file(
    *,
    file: str,
    imported_files_file: str,
    imported_files: list[str],
    local_directory: str,
    ignored_paths: Paths,
    reformat: bool,
    ask_before_artist_update: bool,
    ask_before_disc_update: bool,
    allow_prompt: bool,
    force: bool,
) -> bool | None:
    file = file.strip()
    if (
        Path(file).is_dir()
        or file in ignored_paths
        or not force
        and file in imported_files
    ):
        return None
    try:
        tags = TinyTag.get(file)
        if tags.albumartist:
            artist = tags.albumartist
        elif tags.artist:
            artist = format_field(
                field=tags.artist,
                regex=r"\s\[solo.+\]",
                reformat=reformat,
                confirm_message=get_confirm_message(
                    ask=ask_before_artist_update,
                    message=f"Would you like to remove the bracketed instrument from {tags.artist}?",
                ),
                allow_prompt=allow_prompt,
            )
            if artist is None:
                return False
        else:
            artist = "Unknown Artist"
        if tags.album:
            album = format_field(
                field=tags.album,
                regex=r"\s\[\d{4}(\s(.*EP|.*single))?\]",
                reformat=reformat,
                confirm_message=get_confirm_message(
                    ask=ask_before_disc_update,
                    message=f"Would you like to remove the bracketed year from {tags.album}?",
                ),
                allow_prompt=allow_prompt,
            )
            if album is None:
                return False
        else:
            album = "Unknown Album"
        album = tags.album or "Unknown Album"
        track = Path(artist) / album / Path(file).name
        display_message("Importing", str(track))
        local_path = Path(local_directory) / track
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if local_path.exists():
            existing_track = next(
                (
                    file
                    for file in listdir(local_path.parent)
                    if re.compile(r"__\d+").search(file)
                    and (tags.title or Path(file).stem) in file
                ),
                None,
            )
            if existing_track:
                count = int(existing_track.split("__")[1].split(".")[0])
                local_path = (
                    local_path.parent
                    / f"{local_path.stem}__{count + 1}{local_path.suffix}"
                )
        copy(file, local_path)
        with open(imported_files_file, "a") as log_file:
            log_file.write(f"{file}\n")
        # If reformatting, check and do that here, on the copied version (local_path)
        return True
    except Exception as exception:
        display_message("Error", f"{exception}: {Path(file).name}")
        return None
