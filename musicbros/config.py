from collections.abc import Callable
from configparser import ConfigParser
from pathlib import Path
from subprocess import run
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

from .style import print_with_color

ConfigOption = str
ConfigValue = str
ErrorMessage = str
ConfigOptionAndValue = tuple[ConfigOption, Optional[ConfigValue]]
ConfigOptions = list[ConfigOptionAndValue]

CONFIG_DIRECTORY = Path.home() / ".config" / "musicbros"
CONFIG_FILE = CONFIG_DIRECTORY / "musicbros.ini"
CONFIG_SECTION_NAME = "musicbros"
SHARED_DIRECTORY_OPTION_NAME = "shared_directory"
PICKLE_FILE_OPTION_NAME = "pickle_file"
IGNORED_DIRECTORIES_OPTION_NAME = "ignored_directories"
MUSIC_PLAYER_OPTION_NAME = "music_player"
CONFIG_OPTIONS = [
    SHARED_DIRECTORY_OPTION_NAME,
    PICKLE_FILE_OPTION_NAME,
    IGNORED_DIRECTORIES_OPTION_NAME,
    MUSIC_PLAYER_OPTION_NAME,
]


if not CONFIG_DIRECTORY.exists():
    Path.mkdir(CONFIG_DIRECTORY, parents=True)
if not CONFIG_FILE.is_file():
    with open(CONFIG_FILE, "w") as config_file:
        config_file.write(f"[{CONFIG_SECTION_NAME}]\n")


def get_config_file() -> ConfigParser:
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return config


def get_new_config_value(
    option: ConfigOption, first_time: bool
) -> Optional[ConfigValue]:
    option_display = option.replace("_", " ").upper()
    updating = True
    if not first_time:
        confirm_message = f"Would you like to update the {option_display} value?"
        updating = Confirm.ask(confirm_message)
    is_list_option = option == IGNORED_DIRECTORIES_OPTION_NAME
    clear = False
    empty_value = None
    confirm_clear = not first_time and updating and is_list_option
    if confirm_clear:
        clear = Confirm.ask("Would you like to CLEAR the existing list?")
        if clear:
            empty_value = ""
    if updating:
        prompt_message = f"Please provide your {option_display} value"
        return Prompt.ask(prompt_message)
    return empty_value


def get_config_value(
    option: ConfigOption,
    config: Optional[ConfigParser] = None,
    new=False,
    first_time=False,
) -> Optional[ConfigValue]:
    if new:
        return get_new_config_value(option, first_time)
    if not config:
        config = get_config_file()
    return config.get(CONFIG_SECTION_NAME, option)


def get_option_and_value(
    option: ConfigOption,
    config: Optional[ConfigParser] = None,
    new=False,
    first_time=False,
) -> ConfigOptionAndValue:
    value = get_config_value(option, config, new=new, first_time=first_time)
    return (option, value)


def get_config_options() -> ConfigOptions:
    config = get_config_file()
    options = config.options(CONFIG_SECTION_NAME)
    return [get_option_and_value(option, config) for option in options]


def write_config_options(first_time=False) -> ConfigOptions:
    new_options_and_Values = [
        get_option_and_value(option, new=True, first_time=first_time)
        for option in CONFIG_OPTIONS
    ]
    if first_time:
        config = ConfigParser()
        config[CONFIG_SECTION_NAME] = {}
    else:
        config = get_config_file()
    for option, value in new_options_and_Values:
        if value is not None:
            config[CONFIG_SECTION_NAME][option] = value
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)
    return get_config_options()


def print_config_values():
    console = Console()
    with open(CONFIG_FILE) as config_file:
        syntax = Syntax(config_file.read(), "yaml")
    console.print(syntax)


def update_or_print_config(update: bool):
    if update:
        write_config_options()
    print_config_values()


def get_shared_directory() -> Optional[ConfigValue]:
    return get_config_value(SHARED_DIRECTORY_OPTION_NAME)


def get_pickle_file() -> Optional[ConfigValue]:
    return get_config_value(PICKLE_FILE_OPTION_NAME)


def get_ignored_directories() -> list[ConfigValue]:
    ignored_directories_value = get_config_value(IGNORED_DIRECTORIES_OPTION_NAME)
    if ignored_directories_value:
        ignored_directories = ignored_directories_value.split(",")
    else:
        ignored_directories = []
    return [directory for directory in ignored_directories]


def get_music_player() -> Optional[ConfigValue]:
    return get_config_value(MUSIC_PLAYER_OPTION_NAME)


def add_missing_config_option(option: ConfigOption, value: ConfigValue) -> ConfigValue:
    option_and_value = f"{option} = {value}\n"
    with open(CONFIG_FILE, "a") as config_file:
        config_file.write(option_and_value)
    return value


def validate_shared_directory(shared_directory: ConfigValue) -> Optional[ErrorMessage]:
    shared_directory_exists = Path(shared_directory).is_dir()
    if not shared_directory_exists:
        return (
            "ERROR: Shared directory does not exist. Please create the directory or"
            f" update your config with `{CONFIG_SECTION_NAME} config --update`."
        )
    return None


def validate_pickle_file(pickle_file: ConfigValue) -> Optional[ErrorMessage]:
    pickle_file_exists = Path(pickle_file).is_file()
    if not pickle_file_exists:
        return (
            "ERROR: Pickle file does not exist. Please initialize your beets library"
            " following the beets documentation."
        )
    return None


def validate_music_player(music_player: ConfigValue) -> Optional[ErrorMessage]:
    command = f'mdfind "kMDItemKind == \'Application\'" | grep "{music_player}"'
    application = run(command, shell=True, capture_output=True).stdout
    if not application:
        return (
            "ERROR: Music player does not exist. Please install it or"
            f" update your config with `{CONFIG_SECTION_NAME} config --update`."
        )
    return None


def validate_option(
    value: ConfigValue, option_getter: Callable
) -> Optional[ErrorMessage]:
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
    config_getter: Callable, option: ConfigOption, value: ConfigValue
) -> Optional[ErrorMessage]:
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
