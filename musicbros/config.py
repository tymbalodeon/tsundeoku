from collections.abc import Callable
from configparser import ConfigParser
from pathlib import Path
from subprocess import run
from typing import Optional

from typer import Exit, confirm, echo, prompt

from .helpers import Color, color, create_directory

ConfigOptions = list[tuple[str, str]]
CONFIG_DIRECTORY = create_directory(Path.home() / ".config" / "musicbros")
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
        config_file.write("[musicbros]\n")


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
    if replacing:
        return prompt(prompt_message)
    else:
        return f"{get_config_option(option)},{prompt(prompt_message)}"


def get_new_config_vlue(option: str, first_time: bool) -> Optional[str]:
    clear = False
    replacing = True
    list_option = option != PICKLE_FILE_OPTION_NAME
    option_display = option.replace("_", " ").upper()
    confirm_message = f"Would you like to update the {option_display} value?"
    updating = True if first_time else confirm(confirm_message)
    if not first_time and updating and list_option:
        clear = confirm("Would you like to CLEAR the existing list?")
        if clear:
            replacing = confirm("Would you like to ADD a new value?")
    empty_value = "" if clear else None
    if updating:
        return get_new_value(option, option_display, replacing)
    else:
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
    echo(
        f"A config file is required. Please create one at {CONFIG_FILE} and try again."
    )


def confirm_create_config() -> Optional[ConfigOptions]:
    if confirm("Config file not found. Would you like to create one now?"):
        return write_config_options(first_time=True)
    else:
        return print_create_config_message()


def get_musicbros_config() -> Optional[ConfigOptions]:
    if CONFIG_FILE.is_file():
        return get_config_options()
    else:
        return confirm_create_config()


def print_config_values():
    config = get_musicbros_config()
    if config:
        echo(f"[{color('musicbros')}]")
        for option, value in config:
            echo(f"{color(option, Color.CYAN)} = {value}")


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
    config = get_config()
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
    if shared_directory_exists:
        return None
    return (
        "ERROR: Shared directory does not exist. Please create the directory or"
        f" update your config with `{CONFIG_SECTION_NAME} config --update`."
    )


def validate_pickle_file(pickle_file: str) -> Optional[str]:
    pickle_file_exists = Path(pickle_file).is_file()
    if pickle_file_exists:
        return None
    return (
        "ERROR: Pickle file does not exist. Please initialize your beets library"
        " following the beets documentation."
    )


def validate_music_player(music_player: str) -> Optional[str]:
    command = f'mdfind "kMDItemKind == \'Application\'" | grep "{music_player}"'
    application = run(command, shell=True, capture_output=True).stdout
    if application:
        return None
    return (
        "ERROR: Music player does not exist. Please install it or"
        f" update your config with `{CONFIG_SECTION_NAME} config --update`."
    )


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


def validate_config():
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
    if error_messages:
        for message in error_messages:
            echo(color(message))
        raise Exit()
