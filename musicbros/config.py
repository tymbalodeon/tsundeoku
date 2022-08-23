from configparser import ConfigParser
from json import loads
from pathlib import Path
from subprocess import run
from typing import Optional

from rich import print
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

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
CONFIG_OPTIONS = (
    SHARED_DIRECTORY_OPTION_NAME,
    PICKLE_FILE_OPTION_NAME,
    IGNORED_DIRECTORIES_OPTION_NAME,
    MUSIC_PLAYER_OPTION_NAME,
)


def get_config_directory() -> Path:
    config_directory = Path.home() / CONFIG_PATH
    if not config_directory.exists():
        Path.mkdir(config_directory, parents=True)
    return config_directory


def get_default_shared_directory() -> str:
    return str(Path.home() / "Dropbox")


def get_default_pickle_file() -> str:
    return str(Path.home() / ".config/beets/state.pickle")


def get_config_file() -> Path:
    config_directory = get_config_directory()
    config_file = config_directory / "musicbros.ini"
    if not config_file.is_file():
        section = f"[{CONFIG_SECTION_NAME}]"
        default_shared_directory = get_default_shared_directory()
        default_pickle_file = get_default_pickle_file()
        default_ignored_directories: list[str] = []
        default_music_player = "Swinsian"
        config_base = (
            f"{section}\n"
            f"{SHARED_DIRECTORY_OPTION_NAME} = {default_shared_directory}\n"
            f"{PICKLE_FILE_OPTION_NAME} = {default_pickle_file}\n"
            f"{IGNORED_DIRECTORIES_OPTION_NAME} = {default_ignored_directories}\n"
            f"{MUSIC_PLAYER_OPTION_NAME} = {default_music_player}\n"
        )
        config_file.write_text(config_base)
    return config_file


def get_config() -> ConfigParser:
    config = ConfigParser()
    config_file = get_config_file()
    config.read(config_file)
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
        config = get_config()
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
    config = get_config()
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
        config = get_config()
    for option, value in new_options_and_Values:
        if value is not None:
            config[CONFIG_SECTION_NAME][option] = value
    config_file_path = get_config_file()
    with open(config_file_path, "w") as config_file:
        config.write(config_file)
    return get_config_options()


def print_config_values():
    config_file_path = get_config_file()
    config_path = str(config_file_path)
    syntax = Syntax.from_path(config_path, lexer="yaml", theme="ansi_dark")
    print(f"{config_path}\n")
    print(syntax)


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


def validate_music_player() -> Optional[ErrorMessage]:
    music_player = get_music_player()
    error_message = (
        "ERROR: Music player does not exist. Please install it or"
        f" update your config with `{CONFIG_SECTION_NAME} config --update`."
    )
    if not music_player:
        return error_message
    command = f'mdfind "kMDItemKind == \'Application\'" | grep "{music_player}"'
    application = run(command, shell=True, capture_output=True).stdout
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
