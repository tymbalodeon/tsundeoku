from os import environ
from pathlib import Path
from subprocess import call

from pydantic import BaseModel
from rich import print
from rich.markup import escape
from rich.prompt import Confirm
from typer import Context, Option, Typer, launch

from .config import (
    InvalidConfig,
    get_config_path,
    get_loaded_config,
    print_config_values,
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


def as_paths(paths: list[str]) -> set[Path]:
    return {Path(path).expanduser() for path in paths if path}


def append_directories(existing_values: set[Path], new_values: set[Path]) -> set[Path]:
    return existing_values | new_values


def get_new_directory_values(
    section: set[Path], values: list[str], add: bool
) -> set[Path]:
    new_values = as_paths(values)
    if add:
        return append_directories(section, new_values)
    else:
        return new_values


def no_updates_provided(options: dict) -> bool:
    return all(option is None or option == () for option in options.values())


def print_config_section(section: BaseModel):
    for key, value in section.dict().items():
        if isinstance(value, set):
            value = {path.as_posix() for path in value}
        print(f"{key}={value}")


@config_command.command()
def file_system(
    context: Context,
    shared_directories: list[str] = Option(
        None, help="New shared directories to add to or replace the existing value."
    ),
    pickle_file: str = Option(
        None, help="New path to beets pickle file to replace the existing value."
    ),
    ignored_directories: list[str] = Option(
        None, help="New ignored directories to add to or replace the existing value."
    ),
    music_player: str = Option(
        None, help="New default music player to replace the existing value."
    ),
    add: bool = Option(
        None,
        "--add",
        "-a",
        help="Add to existing values rather than replace all values.",
    ),
):
    """Show and set values for the file-system."""
    config = get_loaded_config()
    file_system = config.file_system
    if no_updates_provided(context.params):
        print_config_section(file_system)
        return
    if shared_directories:
        file_system.shared_directories = get_new_directory_values(
            file_system.shared_directories, shared_directories, add=add
        )
    if pickle_file:
        file_system.pickle_file = Path(pickle_file)
    if ignored_directories:
        file_system.ignored_directories = get_new_directory_values(
            file_system.ignored_directories, ignored_directories, add=add
        )
    if music_player is not None:
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
    ),
    ask_before_disc_update: bool = Option(
        None,
        "--ask-before-disc-update/--auto-update-disc",
        help="Set the default value for asking before adding default disc values",
    ),
    ask_before_artist_update: bool = Option(
        None,
        "--ask-before-artist-update/--auto-update-artist",
        help="Set the default value for asking before removing bracket instruments.",
    ),
    allow_prompt: bool = Option(
        None,
        "--allow-prompt/--disallow-prompt",
        help="Set the default for including imports requiring prompt for user input.",
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
