import re
from os import environ
from pathlib import Path
from subprocess import run
from typing import Annotated

from cyclopts import App, Parameter
from rich import print
from rich.syntax import Syntax

from tsundeoku.config.config import (
    ImportConfig,
    ReformatConfig,
    get_config_path,
    get_loaded_config,
    print_config_section,
    write_config_values,
)
from tsundeoku.style import stylize_path

config_app = App(name="config", help="Show (default) and set config values")


@config_app.command
def edit():
    """Open config file in $EDITOR"""
    run([environ.get("EDITOR", "vim"), get_config_path()])


@config_app.command
def path():
    """Show config file path"""
    print(get_config_path())


# TODO
# display defaults if missing from config file
@config_app.command
def show(*, show_secrets=False):
    """
    Show config values

    Parameters
    ----------
    show_secrets: bool
        Show secret config values
    """
    config_path = get_config_path()
    if not config_path.exists():
        return
    config = config_path.read_text()
    if not show_secrets:
        # TODO use capture groups
        config = re.sub('password = ".+"', 'password = "********"', config)
    print(Syntax(config, "toml", theme="ansi_dark"))


@config_app.command
def set():
    pass


def confirm_reset(values: str) -> bool:
    return input(
        f"Are you sure you want to reset your {values} to the default values?"
    ) in {"y", "Y"}


@config_app.default
def main(*, reset_all=False, reset_commands=False):
    """Cyclopts uses this short description for help.

    Parameters
    ----------
    reset_all: bool
        Reset all config values to the default
    reset_commands: bool
        Reset 'import' and 'reformat' settings to the default
    """
    if reset_all and confirm_reset("config"):
        write_config_values()
    elif reset_commands and confirm_reset("command options preferences"):
        config = get_loaded_config()
        config.reformat = ReformatConfig()
        config.import_new = ImportConfig()
        write_config_values(config)


def confirm_update(value: list[str] | str, add=False, remove=False) -> bool:
    if isinstance(value, list):
        value = [stylize_path(path) for path in value]
        value = ", ".join(value)
    if add:
        response = input(f"Are you sure you want to add {value}?")
    elif remove:
        response = input(f"Are you sure you want to remove {value}?")
    response = input(f"Are you sure you want to update with {value}?")
    return response in {"y", "Y"}


def as_paths(paths: list[str]) -> set[Path]:
    return {Path(path).expanduser() for path in paths if path}


def get_new_directory_values(
    section: set[Path], values: list[str], add: bool, remove: bool
) -> set[Path]:
    new_values = as_paths(values)
    if add:
        return section | new_values
    elif remove:
        new_values = section ^ new_values
        if len(new_values) > len(section):
            return section
        else:
            return new_values
    return new_values


def no_updates_provided(options: dict) -> bool:
    return all(option is None or option == () for option in options.values())


@config_app.command()
def file_system(
    shared_directories: list[str] | None = None,
    pickle_file: str | None = None,
    ignored_directories: list[str] | None = None,
    music_player: str | None = None,
    add=False,
    remove=False,
):
    """Show and set values for the file-system.

    Parameters
    ----------
    shared_directories: list[str] | None
        Directories to check for new albums to import
    pickle_file: str | None
        Path to the pickle file used by beets
    ignored_directories: list[str] | None
        Sub-directories to skip when checking for new albums
    music_player: str | None
        Name of the application for opening music files
    add: bool
        (For list[str] values) add to list instead of replacing all values
    remove: bool
        (For list[str] values) remove from list instead of replacing all values
    """
    config = get_loaded_config()
    file_system = config.file_system
    if shared_directories and confirm_update(
        shared_directories, add=add, remove=remove
    ):
        file_system.shared_directories = get_new_directory_values(
            section=file_system.shared_directories,
            values=shared_directories,
            add=add,
            remove=remove,
        )
    if pickle_file and confirm_update(pickle_file):
        file_system.pickle_file = Path(pickle_file)
    if ignored_directories and confirm_update(
        ignored_directories, add=add, remove=remove
    ):
        file_system.ignored_directories = get_new_directory_values(
            section=file_system.ignored_directories,
            values=ignored_directories,
            add=add,
            remove=remove,
        )
    if music_player is not None and confirm_update(music_player):
        file_system.music_player = music_player
    write_config_values(config)
    print_config_section(file_system)


@config_app.command(name="import")
def import_new(
    reformat=False,
    ask_before_disc_update=False,
    ask_before_artist_update=False,
    allow_prompt=False,
):
    """Show and set default values for "import" command.

    Parameters
    ----------
    reformat: bool | None
        Toggle reformatting
    ask_before_disc_update: bool | None
        Toggle confirming disc updates
    ask_before_artist_update: bool | None
        Toggle confirming removal of brackets from artist field
    allow_prompt: bool | None
        Toggle skipping imports that require user input
    """
    config = get_loaded_config()
    import_new = config.import_new
    if reformat is not None:
        import_new.reformat = reformat
    if ask_before_disc_update is not None:
        import_new.ask_before_disc_update = ask_before_disc_update
    if ask_before_artist_update is not None:
        import_new.ask_before_artist_update = ask_before_artist_update
    if allow_prompt is not None:
        import_new.allow_prompt = allow_prompt
    write_config_values(config)
    print_config_section(import_new)


@config_app.command()
def reformat(
    *,
    remove_bracketed_years: Annotated[
        bool | None, Parameter(negative="--keep-bracketed-years")
    ] = None,
    remove_bracketed_instruments: Annotated[
        bool | None, Parameter(negative="--keep-bracketed-years")
    ] = None,
    expand_abbreviations: Annotated[
        bool | None, Parameter(negative="--keep-abbreviations")
    ] = None,
):
    """Show and set default values for "reformat" command.

    Parameters
    ----------
    remove_bracketed_years: bool | None
        Toggle removing bracketed years
    remove_bracketed_instruments: bool | None
        Toggle removing bracketed instruments
    expand_abbreviations: bool | None
        Toggle expanding abbreviations
    """
    config = get_loaded_config()
    reformat = config.reformat
    if remove_bracketed_years is not None:
        reformat.remove_bracket_years = remove_bracketed_years
    if remove_bracketed_instruments is not None:
        reformat.remove_bracket_instruments = remove_bracketed_instruments
    if expand_abbreviations is not None:
        reformat.expand_abbreviations = expand_abbreviations
    write_config_values(config)
    print_config_section(reformat)


@config_app.command()
def notifications(
    username: str | None = None,
    password: str | None = None,
    *,
    email_on: Annotated[
        bool | None, Parameter(negative="--email-off")
    ] = False,
    system_on: Annotated[
        bool | None, Parameter(negative="--system-off")
    ] = False,
):
    """Show and set values for notifications from scheduled import command.

    Parameters
    ----------
    username: str | None
        Set username for sending email notifications
    password: bool | None
        Set password for sending email notifications
    email_on: bool | None
        Toggle email notifications
    system_on: bool | None
        Toggle system notifications
    """
    config = get_loaded_config()
    notifications = config.notifications
    if username is not None:
        notifications.username = username
    if password is not None:
        notifications.password = password
    if email_on is not None:
        notifications.email_on = email_on
    if system_on is not None:
        notifications.system_on = system_on
    write_config_values(config)
    print_config_section(notifications)
