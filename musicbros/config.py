from configparser import ConfigParser
from json import loads
from pathlib import Path
from subprocess import run
from typing import Optional

from rich import print

from .style import print_with_color

ConfigOption = str
ConfigValue = str
ErrorMessage = str
ConfigOptionAndValue = tuple[ConfigOption, Optional[ConfigValue]]
ConfigOptions = list[ConfigOptionAndValue]

CONFIG_PATH = ".config/musicbros"
CONFIG_SECTION_NAME = "musicbros"
SHARED_DIRECTORY_OPTION_NAME = "shared_directory"
PICKLE_FILE_OPTION_NAME = "pickle_file"
IGNORED_DIRECTORIES_OPTION_NAME = "ignored_directories"
MUSIC_PLAYER_OPTION_NAME = "music_player"


def get_config_directory() -> Path:
    config_directory = Path.home() / CONFIG_PATH
    if not config_directory.exists():
        Path.mkdir(config_directory, parents=True)
    return config_directory


def get_default_shared_directory() -> str:
    return str(Path.home() / "Dropbox")


def get_default_pickle_file() -> str:
    return str(Path.home() / ".config/beets/state.pickle")


def get_config_path() -> Path:
    config_directory = get_config_directory()
    return config_directory / "musicbros.ini"


def get_config_defaults() -> str:
    default_shared_directory = get_default_shared_directory()
    default_pickle_file = get_default_pickle_file()
    default_ignored_directories: list[str] = []
    default_music_player = "Swinsian"
    return (
        f"{SHARED_DIRECTORY_OPTION_NAME} = {default_shared_directory}\n"
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
    config: Optional[ConfigParser] = None,
) -> Optional[ConfigValue]:
    if not config:
        config = get_config()
    return config.get(CONFIG_SECTION_NAME, option)


def get_option_and_value(
    option: ConfigOption,
    config: Optional[ConfigParser] = None,
) -> ConfigOptionAndValue:
    value = get_config_value(option, config)
    return (option, value)


def get_config_options() -> ConfigOptions:
    config = get_config()
    options = config.options(CONFIG_SECTION_NAME)
    return [get_option_and_value(option, config) for option in options]


def print_config_values():
    config_file_path = get_config_file()
    config = config_file_path.read_text().splitlines()[1:]
    for option in config:
        print(option)


def get_shared_directory() -> Optional[ConfigValue]:
    return get_config_value(SHARED_DIRECTORY_OPTION_NAME)


def get_pickle_file() -> Optional[ConfigValue]:
    return get_config_value(PICKLE_FILE_OPTION_NAME)


def get_ignored_directories() -> list[ConfigValue]:
    ignored_directories = get_config_value(IGNORED_DIRECTORIES_OPTION_NAME)
    if not ignored_directories:
        return []
    return loads(ignored_directories)


def get_music_player() -> Optional[ConfigValue]:
    return get_config_value(MUSIC_PLAYER_OPTION_NAME)


def get_directory_display(directory: Optional[str]) -> str:
    if directory:
        return f' "{directory}" '
    return ""


def get_shared_directory_error_message(shared_directory: Optional[str]) -> ErrorMessage:
    directory_display = get_directory_display(shared_directory)
    return (
        f"ERROR: Shared directory{directory_display}does not exist. Please create the"
        f" directory or update your config with `{CONFIG_SECTION_NAME} config"
        " --update`."
    )


def validate_shared_directory() -> Optional[ErrorMessage]:
    shared_directory = get_shared_directory()
    error_message = get_shared_directory_error_message(shared_directory)
    if not shared_directory or not Path(shared_directory).is_dir():
        return error_message
    return None


def get_ignored_directory_error_message(
    ignored_directory: Optional[str],
) -> ErrorMessage:
    directory_display = get_directory_display(ignored_directory)
    return (
        f"ERROR: Ignored directory{directory_display}does not exist. Please add a valid"
        f" directory  to your config with `{CONFIG_SECTION_NAME} config --update`."
    )


def validate_ignored_directories() -> Optional[ErrorMessage]:
    ignored_directories = get_ignored_directories()
    if not ignored_directories:
        return None
    for directory in ignored_directories:
        if not Path(directory).is_dir():
            error_message = get_ignored_directory_error_message(directory)
            return error_message
    return None


def validate_pickle_file() -> Optional[ErrorMessage]:
    pickle_file = get_pickle_file()
    error_message = (
        "ERROR: Pickle file does not exist. Please initialize your beets library by"
        " following the instructions in the"
        " [link=https://beets.readthedocs.io/en/stable/]beets documentation.[/link]"
    )
    if not pickle_file or not Path(pickle_file).is_file():
        return error_message
    return None


def application_exists(command):
    return run(command, shell=True, capture_output=True).stdout


def validate_music_player() -> Optional[ErrorMessage]:
    music_player = get_music_player()
    error_message = (
        "ERROR: Music player does not exist. Please install it or"
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
    validators = [
        validate_shared_directory,
        validate_pickle_file,
        validate_ignored_directories,
        validate_music_player,
    ]
    for validate in validators:
        error_message = validate()
        if error_message:
            error_messages.append(error_message)
    for message in error_messages:
        print_with_color(message)
    return not error_messages
