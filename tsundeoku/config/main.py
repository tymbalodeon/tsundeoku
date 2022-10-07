from os import environ
from pathlib import Path
from subprocess import run

from rich import print
from rich.markup import escape
from rich.prompt import Confirm
from typer import Context, Option, Typer, launch

from tsundeoku.style import stylize_path

from .config import (
    ImportConfig,
    InvalidConfig,
    ReformatConfig,
    confirm_reset,
    get_config_path,
    get_loaded_config,
    print_config_section,
    print_config_values,
    write_config_values,
)

config_command = Typer(
    help=f"Show {escape('[default]')} and set config values.",
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
    reset_all: bool = Option(
        False, "--reset-all", help="Reset all config values to defaults."
    ),
    reset_commands: bool = Option(
        False,
        "--reset-commands",
        help='Reset settings for "import" and "reformat" commands to defaults.',
    ),
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
        run([editor, config_path])
        return
    elif reset_all and confirm_reset():
        try:
            write_config_values()
        except InvalidConfig:
            return
    elif reset_commands and confirm_reset(commands=True):
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
        return Confirm.ask(f"Are you sure you want to add {value}?")
    elif remove:
        return Confirm.ask(f"Are you sure you want to remove {value}?")
    return Confirm.ask(f"Are you sure you want to update with {value}?")


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


@config_command.command()
def file_system(
    context: Context,
    shared_directories: list[str] = Option(
        None,
        help="New shared directories to add to or replace the existing value.",
        show_default=False,
    ),
    pickle_file: str = Option(
        None,
        help="New path to beets pickle file to replace the existing value.",
        show_default=False,
    ),
    ignored_directories: list[str] = Option(
        None,
        help="New ignored directories to add to or replace the existing value.",
        show_default=False,
    ),
    music_player: str = Option(
        None,
        help="New default music player to replace the existing value.",
        show_default=False,
    ),
    add: bool = Option(
        None,
        "--add",
        "-a",
        help="Add to existing values rather than replace all values.",
    ),
    remove: bool = Option(
        None,
        "--remove",
        "-r",
        help="Remove from existing values rather than replace all values.",
    ),
):
    """Show and set values for the file-system."""
    config = get_loaded_config()
    file_system = config.file_system
    if no_updates_provided(context.params):
        print_config_section(file_system)
        return
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


@config_command.command(name="import")
def import_new(
    context: Context,
    reformat: bool = Option(
        None,
        "--reformat/--as-is",
        help='Set the default value for automatically calling "reformat" after import',
        show_default=False,
    ),
    ask_before_disc_update: bool = Option(
        None,
        "--ask-before-disc-update/--auto-update-disc",
        help="Set the default value for asking before adding default disc values",
        show_default=False,
    ),
    ask_before_artist_update: bool = Option(
        None,
        "--ask-before-artist-update/--auto-update-artist",
        help="Set the default value for asking before removing bracket instruments.",
        show_default=False,
    ),
    allow_prompt: bool = Option(
        None,
        "--allow-prompt/--disallow-prompt",
        help="Set the default for including imports requiring prompt for user input.",
        show_default=False,
    ),
):
    """Show and set default values for "import" command."""
    config = get_loaded_config()
    import_new = config.import_new
    if no_updates_provided(context.params):
        print_config_section(import_new)
        return
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


@config_command.command()
def reformat(
    context: Context,
    remove_bracket_years: bool = Option(
        None,
        "--remove-bracket-years/--years-as-is",
        help="Set default value for removing bracket years.",
    ),
    remove_bracket_instruments: bool = Option(
        None,
        "--remove-bracket-instruments/--instruments-as-is",
        help="Set default value for removing bracket instruments.",
    ),
    expand_abbreviations: bool = Option(
        None,
        "--expand-abbreviations/--abbreviations-as-is",
        help="Set default value for expanding abbreviations.",
    ),
):
    """Show and set default values for "reformat" command."""
    config = get_loaded_config()
    reformat = config.reformat
    if no_updates_provided(context.params):
        print_config_section(reformat)
        return
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


@config_command.command()
def notifications(
    context: Context,
    username: str = Option(
        None,
        "--username",
        help="Set email username for sending notifications.",
        show_default=False,
    ),
    password: str = Option(
        None,
        "--password",
        help="Set email password for sending notifications.",
        show_default=False,
    ),
    email_on: bool = Option(
        None,
        "--email-on/--email-off",
        help="Turn email notifications from scheduled imports on or off.",
    ),
    system_on: bool = Option(
        None,
        "--system-on/--system-off",
        help="Turn system notifications from scheduled imports on or off.",
    ),
):
    """Show and set values for notifications from scheduled import command."""
    config = get_loaded_config()
    notifications = config.notifications
    if no_updates_provided(context.params):
        print_config_section(notifications)
        return
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
