from os import environ
from subprocess import call
from pathlib import Path
from pydantic import ValidationError

from rich import print
from rich.markup import escape
from rich.prompt import Confirm
from typer import Argument, Context, Option, Typer, launch

from .config import (
    Config,
    StyleLevel,
    get_config,
    get_config_path,
    get_ignored_directories,
    get_music_player,
    get_pickle_file,
    get_shared_directories,
    print_config_values,
    print_with_theme,
    write_config_values,
)

config_app = Typer(
    help=(
        f"Show config {escape('[default]')}, show config path, edit config file"
        " in $EDITOR"
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)


@config_app.callback(invoke_without_command=True)
def config(
    context: Context,
    path: bool = Option(False, "--path", "-p", help="Show config file path."),
    file: bool = Option(
        False, "--file", "-f", help="Open config file in file browser."
    ),
    edit: bool = Option(False, "--edit", "-e", help="Edit config file with $EDITOR."),
    reset: bool = Option(False, "--reset", help="Reset config to defaults."),
):
    if context.invoked_subcommand:
        return
    config_path = get_config_path()
    if path:
        print(config_path)
    elif file:
        launch(str(config_path), locate=True)
    elif edit:
        editor = environ.get("EDITOR", "vim")
        call([editor, config_path])
    elif reset:
        perform_reset = Confirm.ask(
            "Are you sure you want to reset your config to the default values?"
        )
        if perform_reset:
            print("Config reset.")
            write_config_values()
    else:
        print_config_values()


def as_posix(directories: set[Path]) -> set[str]:
    return {path.as_posix() for path in directories}


def as_path(directories: set[str]) -> set[Path]:
    return {Path(path) for path in directories}


def append_new_directories(
    existing_values: set[Path], new_values: list[str]
) -> set[Path]:
    existing_directories = as_posix(existing_values)
    new_directories = existing_directories | set(new_values)
    return as_path(new_directories)


def replace_directories(new_values: list[str]) -> set[Path]:
    return as_path(set(new_values))


def print_directories(directories: set[Path]):
    display = as_posix(directories) or None
    print(display)


def validate_config(config: Config) -> Config | None:
    try:
        config = Config(**config.dict())
        return config
    except ValidationError as error:
        errors = error.errors()
        for error in errors:
            message = f"ERROR: {error['msg']}"
            print_with_theme(message, level=StyleLevel.ERROR)
        return None


@config_app.command()
def shared_directories(
    new_directories: list[str] = Argument(
        None, help="New directories to add to or replace the existing value."
    ),
    add: bool = Option(
        False,
        "--add",
        "-a",
        help="Add to existing values rather than replace all values.",
        hidden=False,
    ),
):
    """Show shared directories value."""
    if not new_directories:
        shared_directories = get_shared_directories()
        print_directories(shared_directories)
        return
    config = get_config()
    if add:
        new_shared_directories = append_new_directories(
            config.shared_directories, new_directories
        )
    else:
        replace = Confirm.ask(
            "Are you sure you want to overwrite the shared directories?"
        )
        if not replace:
            return
        new_shared_directories = replace_directories(new_directories)
    config.shared_directories = new_shared_directories
    validated_config = validate_config(config)
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Shared directories updated.")


@config_app.command()
def pickle_file(
    new_pickle_file: str = Argument(
        None, help="New path to beets pickle file to replace the existing value."
    ),
):
    """Show pickle file value."""
    if not new_pickle_file:
        pickle_file = get_pickle_file()
        print(pickle_file)
        return
    config = get_config()
    replace = Confirm.ask("Are you sure you want to overwrite the pickle file?")
    if not replace:
        return
    config.pickle_file = Path(new_pickle_file)
    validated_config = validate_config(config)
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Pickle file updated.")


@config_app.command()
def ignored_directories(
    new_directories: list[str] = Argument(
        None, help="New directories to add to or replace the existing value."
    ),
    add: bool = Option(
        False,
        "--add",
        "-a",
        help="Add to existing values rather than replace all values.",
        hidden=False,
    ),
):
    """Show ignored directories value."""
    if not new_directories:
        ignored_directories = get_ignored_directories()
        print_directories(ignored_directories)
        return
    config = get_config()
    if add:
        new_ignored_directories = append_new_directories(
            config.ignored_directories, new_directories
        )
    else:
        replace = Confirm.ask(
            "Are you sure you want to overwrite the ignored directories?"
        )
        if not replace:
            return
        new_ignored_directories = replace_directories(new_directories)
    config.ignored_directories = new_ignored_directories
    validated_config = validate_config(config)
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Ignored directories updated.")


@config_app.command()
def music_player(
    new_music_player: str = Argument(
        None, help="New default music player to replace the existing value."
    ),
):
    """Show music player value."""
    if not new_music_player:
        music_player = get_music_player()
        print(music_player)
        return
    config = get_config()
    replace = Confirm.ask("Are you sure you want to overwrite the music player?")
    if not replace:
        return
    config.music_player = new_music_player
    validated_config = validate_config(config)
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Muisc player updated.")
