from configparser import ConfigParser
from pathlib import Path

from typer import confirm, echo, prompt

from .helpers import color

CONFIG_DIRECTORY = Path.home() / ".config" / "musicbros"
CONFIG_FILE = CONFIG_DIRECTORY / "musicbros.ini"
CONFIG_SECTION = "musicbros"
CONFIG_OPTIONS = [
    "shared_directory",
    "pickle_file",
    "ignored_directories",
    "music_player",
]


def create_config_directory():
    if not CONFIG_DIRECTORY.exists():
        Path.mkdir(CONFIG_DIRECTORY, parents=True)


def get_config_option(option):
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return config.get(CONFIG_SECTION, option)


def get_config_options():
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return [
        (option, config.get(CONFIG_SECTION, option))
        for option in config.options(CONFIG_SECTION)
    ]


def get_ignored_directories():
    config = ConfigParser()
    config.read(CONFIG_FILE)
    ignored_directories = get_config_option("ignored_directories")
    return [directory for directory in ignored_directories.split(",")]


def get_new_value(option, option_display, replacing):
    prompt_message = f"Please provide your {option_display} value"
    return (
        prompt(prompt_message)
        if replacing
        else f"{get_config_option(option)},{prompt(prompt_message)}"
    )


def get_new_config_vlue(option, first_time):
    clear = False
    replacing = False
    list_option = option != CONFIG_OPTIONS[1]
    option_display = option.replace("_", " ").upper()
    confirm_message = f"Would you like to update the {option_display} value?"
    updating = True if first_time else confirm(confirm_message)
    if not first_time and updating and list_option:
        clear = confirm(f"Would you like to CLEAR the existing list?")
        if clear:
            replacing = confirm("Would you like to ADD a new value?")
    empty_value = "" if clear else None

    return get_new_value(option, option_display, replacing) if updating else empty_value


def write_config_options(first_time=False):
    create_config_directory()
    new_values = [
        (option, get_new_config_vlue(option, first_time)) for option in CONFIG_OPTIONS
    ]
    config = ConfigParser()
    if first_time:
        config[CONFIG_SECTION] = dict()
    else:
        config.read(CONFIG_FILE)
    for option, value in new_values:
        if value is not None:
            config[CONFIG_SECTION][option] = value
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)
    return get_config_options()


def print_create_config_message():
    echo(
        f"A config file is required. Please create one at {CONFIG_FILE} and try again."
    )


def confirm_create_config():
    return (
        write_config_options(first_time=True)
        if confirm("Config file not found. Would you like to create one now?")
        else print_create_config_message()
    )


def get_musicbros_config():
    return get_config_options() if CONFIG_FILE.is_file() else confirm_create_config()


def print_config_values():
    config = get_musicbros_config()
    if config:
        for option, value in config:
            echo(f"{color(option.replace('_', ' ').upper())}: {value}")


PICKLE_FILE = get_config_option("pickle_file")
SHARED_DIRECTORY = get_config_option("shared_directory")
MUSIC_PLAYER = get_config_option("music_player")
