from configparser import ConfigParser
from pathlib import Path

from typer import confirm, echo, prompt

from .helpers import color

CONFIG_DIRECTORY = Path.home() / ".config" / "musicbros"
CONFIG_FILE = CONFIG_DIRECTORY / "musicbros.ini"
CONFIG_SECTION = "musicbros"
CONFIG_OPTIONS = ["SHARED DIRECTORY", "PICKLE FILE", "SKIP DIRECTORIES"]


def create_config_directory():
    if not CONFIG_DIRECTORY.exists():
        Path.mkdir(CONFIG_DIRECTORY, parents=True)


def get_config_directory():
    create_config_directory()
    return CONFIG_DIRECTORY


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


def write_config_options(first_time=False):
    create_config_directory()

    def get_new_value(option):
        confirm_message = f"Would you like to update the {option} path?"
        prompt_message = f"Please provide your {option} path"
        is_updating = True if first_time else confirm(confirm_message)
        return prompt(prompt_message) if is_updating else ""

    new_values = [(option, get_new_value(option)) for option in CONFIG_OPTIONS]

    config = ConfigParser()
    if first_time:
        config[CONFIG_SECTION] = dict()
    else:
        config.read(CONFIG_FILE)
    for option, value in new_values:
        if value:
            option = option.replace(" ", "_")
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
