from collections.abc import Callable
from configparser import ConfigParser
from pathlib import Path
from subprocess import run
from typing import Optional

from rich import print
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

from .style import print_with_color

ConfigOptions = list[tuple[str, str]]
CONFIG_DIRECTORY = Path.home() / ".config" / "musicbros"
CONFIG_FILE = CONFIG_DIRECTORY / "musicbros.ini"
CONFIG_SECTION_NAME = "musicbros"
SHARED_DIRECTORY_OPTION_NAME = "shared_directory"
PICKLE_FILE_OPTION_NAME = "pickle_file"
IGNORED_DIRECTORIES_OPTION_NAME = "ignored_directories"
MUSIC_PLAYER_OPTION_NAME = "music_player"


if not CONFIG_DIRECTORY.exists():
    Path.mkdir(CONFIG_DIRECTORY, parents=True)
if not CONFIG_FILE.is_file():
    with open(CONFIG_FILE, "w") as config_file:
        config_file.write(f"[{CONFIG_SECTION_NAME}]\n")


def get_config() -> ConfigParser:
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return config


def get_config_option(option: str) -> str:
    config = get_config()
    return config.get(CONFIG_SECTION_NAME, option)


def get_config_options() -> ConfigOptions:
    config = get_config()
    return [
        (option, config.get(CONFIG_SECTION_NAME, option))
        for option in config.options(CONFIG_SECTION_NAME)
    ]


def get_new_value(option: str, option_display: str, replacing: bool) -> str:
    prompt_message = f"Please provide your {option_display} value"
    new_value = Prompt.ask(prompt_message)
    if replacing:
        return new_value
    return f"{get_config_option(option)},{new_value}"


def get_new_config_vlue(option: str, first_time: bool) -> Optional[str]:
    clear = False
    replacing = True
    list_option = option != PICKLE_FILE_OPTION_NAME
    option_display = option.replace("_", " ").upper()
    confirm_message = f"Would you like to update the {option_display} value?"
    updating = True if first_time else Confirm.ask(confirm_message)
    if not first_time and updating and list_option:
        clear = Confirm.ask("Would you like to CLEAR the existing list?")
        if clear:
            replacing = Confirm.ask("Would you like to ADD a new value?")
    empty_value = "" if clear else None
    if updating:
        return get_new_value(option, option_display, replacing)
    return empty_value


def write_config_options(first_time=False) -> ConfigOptions:
    config_options = [
        SHARED_DIRECTORY_OPTION_NAME,
        PICKLE_FILE_OPTION_NAME,
        IGNORED_DIRECTORIES_OPTION_NAME,
        MUSIC_PLAYER_OPTION_NAME,
    ]
    new_values = [
        (option, get_new_config_vlue(option, first_time)) for option in config_options
    ]
    if first_time:
        config = ConfigParser()
        config[CONFIG_SECTION_NAME] = {}
    else:
        config = get_config()
    for option, value in new_values:
        if value is not None:
            config[CONFIG_SECTION_NAME][option] = value
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)
    return get_config_options()


def print_create_config_message():
    print(
        f"A config file is required. Please create one at {CONFIG_FILE} and try again."
    )


def confirm_create_config() -> Optional[ConfigOptions]:
    if Confirm.ask("Config file not found. Would you like to create one now?"):
        return write_config_options(first_time=True)
    return print_create_config_message()


def get_musicbros_config() -> Optional[ConfigOptions]:
    if not CONFIG_FILE.is_file():
        return confirm_create_config()
    return get_config_options()


def print_config_values():
    config = get_musicbros_config()
    if config:
        console = Console()
        with open(CONFIG_FILE) as config_file:
            syntax = Syntax(config_file.read(), "yaml")
        console.print(syntax)


def update_or_print_config(update: bool):
    if update:
        write_config_options()
    print_config_values()


def get_config_value(option_name: str) -> str:
    return get_config_option(option_name)


def get_shared_directory() -> str:
    return get_config_value(SHARED_DIRECTORY_OPTION_NAME)


def get_pickle_file() -> str:
    return get_config_value(PICKLE_FILE_OPTION_NAME)


def get_ignored_directories() -> list[str]:
    ignored_directories = get_config_option(IGNORED_DIRECTORIES_OPTION_NAME)
    return [directory for directory in ignored_directories.split(",")]


def get_music_player() -> str:
    return get_config_value(MUSIC_PLAYER_OPTION_NAME)


def add_missing_config_option(option: str, value: str) -> str:
    option_and_value = f"{option} = {value}\n"
    with open(CONFIG_FILE, "a") as config_file:
        config_file.write(option_and_value)
    return value


def validate_shared_directory(shared_directory: str) -> Optional[str]:
    shared_directory_exists = Path(shared_directory).is_dir()
    if not shared_directory_exists:
        return (
            "ERROR: Shared directory does not exist. Please create the directory or"
            f" update your config with `{CONFIG_SECTION_NAME} config --update`."
        )
    return None


def validate_pickle_file(pickle_file: str) -> Optional[str]:
    pickle_file_exists = Path(pickle_file).is_file()
    if not pickle_file_exists:
        return (
            "ERROR: Pickle file does not exist. Please initialize your beets library"
            " following the beets documentation."
        )
    return None


def validate_music_player(music_player: str) -> Optional[str]:
    command = f'mdfind "kMDItemKind == \'Application\'" | grep "{music_player}"'
    application = run(command, shell=True, capture_output=True).stdout
    if not application:
        return (
            "ERROR: Music player does not exist. Please install it or"
            f" update your config with `{CONFIG_SECTION_NAME} config --update`."
        )
    return None


def validate_option(value: str, option_getter: Callable) -> Optional[str]:
    validators = {
        get_shared_directory: validate_shared_directory,
        get_pickle_file: validate_pickle_file,
        get_ignored_directories: None,
        get_music_player: validate_music_player,
    }
    validator = validators.get(option_getter)
    if not validator:
        return None
    return validator(value)


def get_or_add_config_option(
    config_getter: Callable, option: str, value: str
) -> Optional[str]:
    try:
        value = config_getter()
    except Exception:
        value = add_missing_config_option(option, value)
    return validate_option(value, config_getter)


def validate_config() -> bool:
    home = Path.home()
    default_shared_directory = str(home / "Dropbox")
    default_pickle_file = str(home / ".config/beets/state.pickle")
    default_music_player = "Swinsian"
    config_getters_and_values = (
        (get_shared_directory, "shared_directory", default_shared_directory),
        (get_pickle_file, "pickle_file", default_pickle_file),
        (get_ignored_directories, "ignored_directories", ""),
        (get_music_player, "music_player", default_music_player),
    )
    error_messages = []
    for option_getter, option, value in config_getters_and_values:
        error_message = get_or_add_config_option(option_getter, option, value)
        if error_message:
            error_messages.append(error_message)
    for message in error_messages:
        print_with_color(message)
    return not error_messages
