from os import environ
from pathlib import Path
from subprocess import call

from rich import print
from rich.markup import escape
from rich.prompt import Confirm
from typer import Argument, Context, Option, Typer, launch

from .config import (
    get_config_path,
    get_loaded_config,
    get_loaded_theme,
    print_config_values,
    validate_config,
    validate_theme_config,
    write_config_values,
)

config_command = Typer(
    help=(
        f"Show config {escape('[default]')}, show config path, edit config file"
        " in $EDITOR"
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)


@config_command.callback(invoke_without_command=True)
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


def append_directories(existing_values: set[Path], new_values: list[str]) -> list[str]:
    existing_directories = as_posix(existing_values)
    new_directories = existing_directories | set(new_values)
    return list(new_directories)


def print_directories(directories: set[Path]):
    display = as_posix(directories) or None
    print(display)


@config_command.command()
def shared_directories(
    directories: list[str] = Argument(
        None, help="New directories to add to or replace the existing value."
    ),
    add: bool = Option(
        False,
        "--add",
        "-a",
        help="Add to existing values rather than replace all values.",
    ),
):
    """Show shared directories value."""
    config = get_loaded_config()
    if not directories:
        shared_directories = config.shared_directories
        print_directories(shared_directories)
        return
    config = config.dict()
    shared_directories = config["shared_directories"]
    if add:
        new_shared_directories = append_directories(shared_directories, directories)
    else:
        replace = Confirm.ask(
            "Are you sure you want to overwrite the shared directories?"
        )
        if not replace:
            return
        new_shared_directories = directories
    config["shared_directories"] = new_shared_directories
    validated_config = validate_config(config)
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Shared directories updated.")


@config_command.command()
def pickle_file(
    pickle_file_path: str = Argument(
        None, help="New path to beets pickle file to replace the existing value."
    ),
):
    """Show pickle file value."""
    config = get_loaded_config()
    if not pickle_file_path:
        pickle_file = config.pickle_file
        print(pickle_file)
        return
    replace = Confirm.ask("Are you sure you want to overwrite the pickle file?")
    if not replace:
        return
    config.pickle_file = Path(pickle_file_path)
    validated_config = validate_config(config.dict())
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Pickle file updated.")


@config_command.command()
def ignored_directories(
    directories: list[str] = Argument(
        None, help="New directories to add to or replace the existing value."
    ),
    add: bool = Option(
        False,
        "--add",
        "-a",
        help="Add to existing values rather than replace all values.",
    ),
):
    """Show ignored directories value."""
    if not directories:
        config = get_loaded_config()
        ignored_directories = config.ignored_directories
        print_directories(ignored_directories)
        return
    config = get_loaded_config().dict()
    ignored_directories = config["ignored_directories"]
    if add:
        new_ignored_directories = append_directories(ignored_directories, directories)
    else:
        replace = Confirm.ask(
            "Are you sure you want to overwrite the ignored directories?"
        )
        if not replace:
            return
        new_ignored_directories = directories
    config["ignored_directories"] = new_ignored_directories
    validated_config = validate_config(config)
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Ignored directories updated.")


@config_command.command()
def music_player(
    new_music_player: str = Argument(
        None, help="New default music player to replace the existing value."
    ),
):
    """Show music player value."""
    config = get_loaded_config()
    if not new_music_player:
        music_player = config.music_player
        print(music_player)
        return
    replace = Confirm.ask("Are you sure you want to overwrite the music player?")
    if not replace:
        return
    config.music_player = new_music_player
    validated_config = validate_config(config.dict())
    if not validated_config:
        return
    write_config_values(config=validated_config)
    print("Muisc player updated.")


@config_command.command(
    help=(
        f"Show config {escape('[default]')}, show config path, edit config file"
        " in $EDITOR"
    )
)
def theme(
    info: str = Option(
        None, "--info", "-i", help='Update the style for "INFO"-level messages'
    ),
    warning: str = Option(
        None, "--warning", "-w", help='Update the style for "WARNING"-level messages'
    ),
    error: str = Option(
        None, "--error", "-e", help='Update the style for "ERROR"-level messages'
    ),
):
    theme_config = get_loaded_theme()
    if not any([info, warning, error]):
        print(theme_config)
        return
    if info:
        theme_config.info = info
    if warning:
        theme_config.warning = warning
    if error:
        theme_config.error = error
    validated_theme_config = validate_theme_config(theme_config.dict())
    if not validated_theme_config:
        return
    write_config_values(theme=validated_theme_config)
    print("Theme updated.")
