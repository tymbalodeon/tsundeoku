import re
from glob import glob
from os import listdir
from pathlib import Path
from shutil import copy
from typing import Annotated, Literal

from cyclopts import App, Group, Parameter
from cyclopts.config import Toml
from cyclopts.validators import Path as PathValidator
from rich import print
from tinytag import TinyTag

from tsundeoku.config import (
    Config,
    config_app,
    get_app_name,
    get_config_path,
    is_toml,
    parse_path,
)
from tsundeoku.schedule import schedule_app

app = App(
    config=Toml(get_config_path()),
    help="""
積んでおく (tsundeoku) –– "to pile up for later"

Import audio files from a shared folder to a local library""",
)
app.command(config_app)
app.command(schedule_app)


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


global_group = Group("Global", sort_key=0)


def reformat_field(field: str, regex: str) -> str:
    match = re.search(regex, field)
    if match is None:
        return field
    return field.replace(match.group(), "")


@app.command(name="import")
def import_command(
    *,
    shared_directories: Annotated[
        tuple[str, ...], Parameter(negative=())
    ] = Config().items.import_config.shared_directories,
    ignored_paths: Annotated[
        tuple[str, ...], Parameter(negative=())
    ] = Config().items.import_config.ignored_paths,
    local_directory: Annotated[
        str, Parameter(negative=())
    ] = Config().items.import_config.local_directory,
    reformat: bool = Config().items.import_config.reformat,
    ask_before_artist_update: Annotated[
        bool, Parameter(negative="--auto-update-artist")
    ] = Config().items.import_config.ask_before_artist_update,
    ask_before_disc_update: Annotated[
        bool,
        Parameter(negative="--auto-update-disc"),
    ] = Config().items.import_config.ask_before_disc_update,
    allow_prompt: Annotated[
        bool, Parameter(negative="--disallow-prompt")
    ] = Config().items.import_config.allow_prompt,
    config_path: Annotated[
        Path,
        Parameter(
            converter=parse_path,
            group=global_group,
            validator=(PathValidator(exists=True, dir_okay=False), is_toml),
        ),
    ] = get_config_path(),
    force: Annotated[bool, Parameter(group=global_group, negative=())] = False,
    is_scheduled_run: Annotated[bool, Parameter(show=False)] = False,
):
    """Copy new adds from your shared folder to your local library.

    Parameters
    ----------
    reformat: bool
        Toggle reformatting.
    ask_before_disc_update: bool
        Toggle confirming disc updates.
    ask_before_artist_update: bool
        Toggle confirming removal of brackets from artist field.
    allow_prompt: bool
        Toggle skipping imports that require user input.
    """
    if config_path != get_config_path():
        config = Config.from_toml(config_path)
        shared_directories = config.items.import_config.shared_directories
        ignored_paths = config.items.import_config.ignored_paths
        local_directory = config.items.import_config.local_directory
        reformat = config.items.import_config.reformat
        ask_before_artist_update = (
            config.items.import_config.ask_before_artist_update
        )
        ask_before_disc_update = (
            config.items.import_config.ask_before_disc_update
        )
        allow_prompt = config.items.import_config.allow_prompt
    for directory in shared_directories:
        shared_directory_files = tuple(
            file for file in sorted(glob(f"{directory}/**/*", recursive=True))
        )
        imported_files_file = (
            Path.home() / f".local/share/{get_app_name()}/imported_files"
        )
        if imported_files_file.exists():
            imported_files = imported_files_file.read_text().splitlines()
        else:
            imported_files_file.parent.mkdir(parents=True, exist_ok=True)
            imported_files_file.touch()
            imported_files = []
        for file in imported_files:
            if file not in shared_directory_files:
                imported_files.remove(file)
            imported_files_file.write_text(f"{'\n'.join(imported_files)}\n")
        for file in shared_directory_files:
            file = file.strip()
            if (
                Path(file).is_dir()
                or file in ignored_paths
                or not force
                and file in imported_files
            ):
                continue
            try:
                tags = TinyTag.get(file)
                if tags.albumartist:
                    artist = tags.albumartist
                elif tags.artist:
                    # check conditions for artist reformat from config, params, etc.
                    if reformat:
                        artist = reformat_field(tags.artist, r"\s\[solo.+\]")
                    else:
                        artist = tags.artist
                else:
                    artist = "Unknown Artist"
                if tags.album:
                    # check conditions for album reformat from config, params, etc.
                    if reformat:
                        album = reformat_field(
                            tags.album, r"\s\[\d{4}(\s(.*EP|.*single))?\]"
                        )
                    else:
                        album = tags.album
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
                        count = int(
                            existing_track.split("__")[1].split(".")[0]
                        )
                        local_path = (
                            local_path.parent
                            / f"{local_path.stem}__{count + 1}{local_path.suffix}"
                        )
                copy(file, local_path)
                with open(imported_files_file, "a") as log_file:
                    log_file.write(f"{file}\n")
                # If reformatting, check and do that here, on the copied version (local_path)
            except Exception as exception:
                display_message("Error", f"{exception}: {Path(file).name}")
