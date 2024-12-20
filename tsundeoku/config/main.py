from os import environ
from rich import print
from pathlib import Path
from subprocess import run
from typing import Annotated

from cyclopts import App, Parameter
from tsundeoku.style import stylize_path

from .config import (
    ImportConfig,
    InvalidConfig,
    ReformatConfig,
    get_config_path,
    get_loaded_config,
    print_config_section,
    print_config_values,
    write_config_values,
)

config_app = App(name="config", help="Show (default) and set config values")


def confirm_reset(values: str) -> bool:
    return input(
        f"Are you sure you want to reset your {values} to the default values?"
    ) in {"y", "Y"}


@config_app.command
def main(
    *,
    path: Annotated[bool, Parameter(negative="")] = False,
    edit: Annotated[bool, Parameter(negative="")] = False,
    reset_all: Annotated[bool, Parameter(negative="")] = False,
    reset_commands: Annotated[bool, Parameter(negative="")] = False,
):
    """Cyclopts uses this short description for help.

    Parameters
    ----------
    path: bool
        Show config file path
    edit: bool
        Open config file in $EDITOR
    reset_all: bool
        Reset all config values to the default
    reset_commands: bool
        Reset 'import' and 'reformat' settings to the default
    """
    if path:
        print(get_config_path())
        return
    elif edit:
        editor = environ.get("EDITOR", "vim")
        run([editor, get_config_path()])
        return
    elif reset_all and confirm_reset("config"):
        try:
            write_config_values()
        except InvalidConfig:
            return
    elif reset_commands and confirm_reset("command options preferences"):
        config = get_loaded_config()
        config.reformat = ReformatConfig()
        config.import_new = ImportConfig()
        try:
            write_config_values(config)
        except InvalidConfig:
            return
    print_config_values()


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


# shared_directories: list[str] = Option(
#     None,
#     help="New shared directories to add to or replace the existing value.",
#     show_default=False,
# ),
# pickle_file: str = Option(
#     None,
#     help="New path to beets pickle file to replace the existing value.",
#     show_default=False,
# ),
# ignored_directories: list[str] = Option(
#     None,
#     help=(
#         "New ignored directories to add to or replace the existing value."
#     ),
#     show_default=False,
# ),
# music_player: str = Option(
#     None,
#     help="New default music player to replace the existing value.",
#     show_default=False,
# ),
# add: bool = Option(
#     None,
#     "--add",
#     "-a",
#     help="Add to existing values rather than replace all values.",
# ),
# remove: bool = Option(
#     None,
#     "--remove",
#     "-r",
#     help="Remove from existing values rather than replace all values.",
# ),


@config_app.command()
def file_system(
    shared_directories: list[str] | None = None,
    pickle_file: str | None = None,
    ignored_directories: list[str] | None = None,
    music_player: str | None = None,
    add=False,
    remove=False,
):
    """Show and set values for the file-system."""
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
    try:
        write_config_values(config)
    except InvalidConfig:
        return
    print_config_section(file_system)


# reformat: bool = Option(
#     None,
#     "--reformat/--as-is",
#     help=(
#         'Set the default value for automatically calling "reformat" after'
#         " import"
#     ),
#     show_default=False,
# ),
# ask_before_disc_update: bool = Option(
#     None,
#     "--ask-before-disc-update/--auto-update-disc",
#     help=(
#         "Set the default value for asking before adding default disc"
#         " values"
#     ),
#     show_default=False,
# ),
# ask_before_artist_update: bool = Option(
#     None,
#     "--ask-before-artist-update/--auto-update-artist",
#     help=(
#         "Set the default value for asking before removing bracket"
#         " instruments."
#     ),
#     show_default=False,
# ),
# allow_prompt: bool = Option(
#     None,
#     "--allow-prompt/--disallow-prompt",
#     help=(
#         "Set the default for including imports requiring prompt for user"
#         " input."
#     ),
#     show_default=False,
# ),


@config_app.command(name="import")
def import_new(
    reformat=False,
    ask_before_disc_update=False,
    ask_before_artist_update=False,
    allow_prompt=False,
):
    """Show and set default values for "import" command."""
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
    try:
        write_config_values(config)
    except InvalidConfig:
        return
    print_config_section(import_new)


# remove_bracket_years: bool = Option(
#     None,
#     "--remove-bracket-years/--years-as-is",
#     help="Set default value for removing bracket years.",
# ),
# remove_bracket_instruments: bool = Option(
#     None,
#     "--remove-bracket-instruments/--instruments-as-is",
#     help="Set default value for removing bracket instruments.",
# ),
# expand_abbreviations: bool = Option(
#     None,
#     "--expand-abbreviations/--abbreviations-as-is",
#     help="Set default value for expanding abbreviations.",
# ),


@config_app.command()
def reformat(
    remove_bracket_years=False,
    remove_bracket_instruments=False,
    expand_abbreviations=False,
):
    """Show and set default values for "reformat" command."""
    config = get_loaded_config()
    reformat = config.reformat
    if remove_bracket_years is not None:
        reformat.remove_bracket_years = remove_bracket_years
    if remove_bracket_instruments is not None:
        reformat.remove_bracket_instruments = remove_bracket_instruments
    if expand_abbreviations is not None:
        reformat.expand_abbreviations = expand_abbreviations
    try:
        write_config_values(config)
    except InvalidConfig:
        return
    print_config_section(reformat)


# context: Context,
# username: str = Option(
#     None,
#     "--username",
#     help="Set email username for sending notifications.",
#     show_default=False,
# ),
# password: str = Option(
#     None,
#     "--password",
#     help="Set email password for sending notifications.",
#     show_default=False,
# ),
# email_on: bool = Option(
#     None,
#     "--email-on/--email-off",
#     help="Turn email notifications from scheduled imports on or off.",
# ),
# system_on: bool = Option(
#     None,
#     "--system-on/--system-off",
#     help="Turn system notifications from scheduled imports on or off.",
# ),


@config_app.command()
def notifications(
    username: str | None = None,
    password: str | None = None,
    email_on=False,
    system_on=False,
):
    """Show and set values for notifications from scheduled import command."""
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
    try:
        write_config_values(config)
    except InvalidConfig:
        return
    print_config_section(notifications)
