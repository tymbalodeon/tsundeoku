from collections.abc import Callable
from configparser import ConfigParser
from json import loads
from os import environ
from pathlib import Path
from subprocess import call, run

from rich import print
from rich.markup import escape
from typer import Argument, Context, Option, Typer, launch

from .style import get_theme_config, print_with_color, stylize

ConfigOption = str
ConfigValue = str
ErrorMessage = str
ConfigOptionAndValue = tuple[ConfigOption, ConfigValue | None]
ConfigOptions = list[ConfigOptionAndValue]
Validator = Callable[[], list[ErrorMessage] | ErrorMessage | None]

CONFIG_PATH = ".config/tsundeoku"
CONFIG_SECTION_NAME = "tsundeoku"
SHARED_DIRECTORIES_OPTION_NAME = "shared_directories"
PICKLE_FILE_OPTION_NAME = "pickle_file"
IGNORED_DIRECTORIES_OPTION_NAME = "ignored_directories"
MUSIC_PLAYER_OPTION_NAME = "music_player"

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
    else:
        print_config_values()


def get_config_directory() -> Path:
    config_directory = Path.home() / CONFIG_PATH
    if not config_directory.exists():
        Path.mkdir(config_directory, parents=True)
    return config_directory


def get_default_shared_directories() -> str:
    default_shared_directories = Path.home() / "Dropbox"
    return f'["{default_shared_directories}"]'


def get_default_pickle_file() -> str:
    return str(Path.home() / ".config/beets/state.pickle")


def get_config_path() -> Path:
    config_directory = get_config_directory()
    return config_directory / "tsundeoku.ini"


def get_config_defaults() -> str:
    default_shared_directories = get_default_shared_directories()
    default_pickle_file = get_default_pickle_file()
    default_ignored_directories: list[str] = []
    default_music_player = "Swinsian"
    return (
        f"{SHARED_DIRECTORIES_OPTION_NAME} = {default_shared_directories}\n"
        f"{PICKLE_FILE_OPTION_NAME} = {default_pickle_file}\n"
        f"{IGNORED_DIRECTORIES_OPTION_NAME} = {default_ignored_directories}\n"
        f"{MUSIC_PLAYER_OPTION_NAME} = {default_music_player}\n"
    )


def get_config_file() -> Path:
    config_file = get_config_path()
    if not config_file.is_file():
        section = f"[{CONFIG_SECTION_NAME}]"
        config_defaults = get_config_defaults()
        config_base = f"{section}\n{config_defaults}"
        config_file.write_text(config_base)
    return config_file


def get_config() -> ConfigParser:
    config = ConfigParser()
    config_file = get_config_file()
    config.read(config_file)
    return config


def get_config_value(
    option: ConfigOption,
    config: ConfigParser | None = None,
) -> ConfigValue | None:
    if not config:
        config = get_config()
    return config.get(CONFIG_SECTION_NAME, option)


def get_option_and_value(
    option: ConfigOption,
    config: ConfigParser | None = None,
) -> ConfigOptionAndValue:
    value = get_config_value(option, config)
    return (option, value)


def get_config_options() -> ConfigOptions:
    config = get_config()
    options = config.options(CONFIG_SECTION_NAME)
    return [get_option_and_value(option, config) for option in options]


def print_values(config_path):
    config = config_path.read_text().splitlines()[1:]
    for option in config:
        print(option)


def print_config_values():
    config_path = get_config_file()
    print_values(config_path)


def print_theme_config_values():
    theme_config_path = Path(get_theme_config())
    print_values(theme_config_path)


def get_shared_directories() -> list[ConfigValue]:
    shared_directories = get_config_value(SHARED_DIRECTORIES_OPTION_NAME)
    if not shared_directories:
        return []
    return loads(shared_directories)


def get_pickle_file() -> ConfigValue | None:
    return get_config_value(PICKLE_FILE_OPTION_NAME)


def get_ignored_directories() -> list[ConfigValue]:
    ignored_directories = get_config_value(IGNORED_DIRECTORIES_OPTION_NAME)
    if not ignored_directories:
        return []
    return loads(ignored_directories)


def get_music_player() -> ConfigValue | None:
    return get_config_value(MUSIC_PLAYER_OPTION_NAME)


def get_directory_display(directory: str | None) -> str:
    if directory:
        return f' "{directory}" '
    return ""


def get_shared_directory_error_message(shared_directory: str | None) -> ErrorMessage:
    directory_display = get_directory_display(shared_directory)
    return (
        f"WARNING: Shared directory{directory_display}does not exist. Please create the"
        f" directory or update your config with `{CONFIG_SECTION_NAME} config"
        " --update`."
    )


def get_ignored_directory_error_message(
    ignored_directory: str | None,
) -> ErrorMessage:
    directory_display = get_directory_display(ignored_directory)
    return (
        f"WARNING: Ignored directory{directory_display}does not exist. Please add a"
        f" valid directory  to your config with `{CONFIG_SECTION_NAME} config"
        " --update`."
    )


def get_validate_directories(
    get_directories: Callable[[], list[ConfigValue]],
    get_error_message: Callable[[str | None], ErrorMessage],
) -> Validator:
    def validate_directories() -> list[ErrorMessage] | None:
        directories = get_directories()
        if not directories:
            return None
        error_messages = []
        for directory in directories:
            if not Path(directory).is_dir():
                error_message = get_error_message(directory)
                error_messages.append(error_message)
        return error_messages or None

    return validate_directories


def validate_pickle_file() -> ErrorMessage | None:
    pickle_file = get_pickle_file()
    beets_documentation_link = stylize(
        "beets documentation", "link=https://beets.readthedocs.io/en/stable/"
    )
    error_message = (
        "WARNING: Pickle file does not exist. Please initialize your beets library by"
        " following the instructions in the"
        f"{beets_documentation_link}."
    )
    if not pickle_file or not Path(pickle_file).is_file():
        return error_message
    return None


def application_exists(command):
    return run(command, shell=True, capture_output=True).stdout


def validate_music_player() -> ErrorMessage | None:
    music_player = get_music_player()
    error_message = (
        "WARNING: Music player does not exist. Please install it or"
        f" update your config with `{CONFIG_SECTION_NAME} config --update`."
    )
    if not music_player:
        return error_message
    command = f'mdfind "kMDItemKind == \'Application\'" | grep "{music_player}"'
    application = application_exists(command)
    if not application:
        return error_message
    return None


def validate_config() -> bool:
    error_messages = []
    validate_shared_directories = get_validate_directories(
        get_shared_directories, get_shared_directory_error_message
    )
    validate_ignored_directories = get_validate_directories(
        get_ignored_directories, get_ignored_directory_error_message
    )
    validators = [
        validate_shared_directories,
        validate_pickle_file,
        validate_ignored_directories,
        validate_music_player,
    ]
    for validate in validators:
        error = validate()
        if error:
            if isinstance(error, list):
                error_messages.extend(error)
            else:
                error_messages.append(error)
    for message in error_messages:
        print_with_color(message)
    return not error_messages


@config_app.command()
def shared_directories(
    directories: list[str] = Argument(
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
    shared_directoires = get_shared_directories()
    print(shared_directoires)


@config_app.command()
def pickle_file(
    path: str = Argument(
        None, help="New path to beets pickle file to replace the existing value."
    ),
):
    """Show pickle file value."""
    print(path)
    pickle_file = get_pickle_file()
    print(pickle_file)


@config_app.command()
def ignored_directories(
    directories: list[str] = Argument(
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
    ignored_directories = get_ignored_directories()
    print(ignored_directories)


@config_app.command()
def music_player(
    path: str = Argument(
        None, help="New default music player to replace the existing value."
    ),
):
    """Show music player value."""
    music_player = get_music_player()
    print(music_player)


@config_app.command()
def theme(
    path: bool = Option(False, "--path", "-p", help="Show theme config file path."),
    file: bool = Option(
        False, "--file", "-f", help="Open theme config file in file browser."
    ),
    edit: bool = Option(
        False, "--edit", "-e", help="Edit theme config file with $EDITOR."
    ),
):
    """Show theme config."""
    theme_config = get_theme_config()
    if path:
        print(theme_config)
    elif file:
        launch(theme_config, locate=True)
    elif edit:
        editor = environ.get("EDITOR", "vim")
        call([editor, theme_config])
    else:
        print_theme_config_values()
