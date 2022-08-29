from collections.abc import Callable
from enum import Enum
from os import environ
from pathlib import Path
from subprocess import call, run

from pydantic import BaseModel, Field
from rich import print
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm
from rich.style import Style
from rich.syntax import Syntax
from rich.theme import Theme
from tomli import loads
from tomli_w import dumps
from typer import Argument, Context, Option, Typer, launch

from .style import stylize

APP_NAME = "tsundeoku"
THEME_NAME = "theme"
CONFIG_PATH = f".config/{APP_NAME}"


config_app = Typer(
    help=(
        f"Show config {escape('[default]')}, show config path, edit config file"
        " in $EDITOR"
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)


def get_default_shared_directories() -> list[str]:
    default_shared_directory = str(Path.home() / "Dropbox")
    return [default_shared_directory]


def get_default_pickle_file() -> str:
    return str(Path.home() / ".config/beets/state.pickle")


class Config(BaseModel):
    shared_directories: list[str] = Field(
        default_factory=get_default_shared_directories
    )
    pickle_file: str = Field(default_factory=get_default_pickle_file)
    ignored_directories: list[str] = Field(default_factory=list)
    music_player = "Swinsian"


class ThemeConfig(BaseModel):
    info = "dim cyan"
    warning = "yellow"
    error = "bold red"


def get_config_directory() -> Path:
    config_directory = Path.home() / CONFIG_PATH
    if not config_directory.exists():
        Path.mkdir(config_directory, parents=True)
    return config_directory


def get_config_path() -> Path:
    config_directory = get_config_directory()
    return config_directory / f"{APP_NAME}.toml"


def write_config(**config_and_theme: Config | ThemeConfig):
    if "config" not in config_and_theme:
        config = dict(Config())
    else:
        config = config_and_theme["config"]
    if "theme" not in config_and_theme:
        theme = dict(ThemeConfig())
    else:
        theme = config_and_theme["theme"]
    config = {APP_NAME: config, THEME_NAME: theme}
    config_file = get_config_path()
    config_file.write_text(dumps(config))


def get_config_file() -> Path:
    config_file = get_config_path()
    if not config_file.is_file():
        write_config()
    return config_file


def get_config_text() -> str:
    config_file = get_config_file()
    return config_file.read_text()


def read_config_values() -> dict[str, list[Path] | Path | str]:
    config_text = get_config_text()
    return loads(config_text)[APP_NAME]


def read_theme_config_values() -> dict[str, str]:
    config_text = get_config_text()
    return loads(config_text)[THEME_NAME]


def get_config() -> Config:
    config_values = read_config_values()
    return Config(**config_values)


def get_theme_config() -> ThemeConfig:
    theme_config_values = read_theme_config_values()
    return ThemeConfig(**theme_config_values)


def get_theme() -> Theme:
    theme_config_values = read_theme_config_values()
    return Theme(theme_config_values)


class StyleLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def get_style(level: StyleLevel) -> Style:
    theme = get_theme()
    return theme.styles[level.value]


def print_with_theme(text: Syntax | str, level: StyleLevel | None = None):
    theme = get_theme()
    console = Console(theme=theme)
    if level:
        style = get_style(level)
        console.print(text, style=style)
    else:
        console.print(text)


def print_config_values():
    config_file = str(get_config_file())
    syntax = Syntax.from_path(config_file, lexer="toml", theme="ansi_dark")
    print_with_theme(syntax)


def get_shared_directories() -> list[Path]:
    config = get_config()
    return [Path(path) for path in config.shared_directories]


def get_pickle_file() -> Path:
    config = get_config()
    return Path(config.pickle_file)


def get_ignored_directories() -> list[Path]:
    config = get_config()
    return [Path(path) for path in config.ignored_directories]


def get_music_player() -> str:
    config = get_config()
    return config.music_player


def get_directory_display(directory: Path) -> str:
    return f' "{directory}" '


def get_shared_directory_error_message(shared_directory: Path) -> str:
    directory_display = get_directory_display(shared_directory)
    return (
        f"WARNING: Shared directory{directory_display}does not exist. Please create the"
        f" directory or update your config with `{APP_NAME} config"
        " --update`."
    )


def get_ignored_directory_error_message(ignored_directory: Path) -> str:
    directory_display = get_directory_display(ignored_directory)
    return (
        f"WARNING: Ignored directory{directory_display}does not exist. Please add a"
        f" valid directory  to your config with `{APP_NAME} config"
        " --update`."
    )


def get_validate_directories(
    get_directories: Callable[[], list[Path]],
    get_error_message: Callable[[Path], str],
) -> Callable[[], list[str] | str | None]:
    def validate_directories() -> list[str] | None:
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


def validate_pickle_file() -> str | None:
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


def validate_music_player() -> str | None:
    music_player = get_music_player()
    error_message = (
        "WARNING: Music player does not exist. Please install it or"
        f" update your config with `{APP_NAME} config --update`."
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
        print_with_theme(message, level=StyleLevel.WARNING)
    return not error_messages


@config_app.callback(invoke_without_command=True)
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
            write_config()
    else:
        print_config_values()


@config_app.command()
def shared_directories(
    new_directories: list[str] = Argument(
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
    if new_directories:
        config = get_config()
        if add:
            shared_directories = set(config.shared_directories)
            for directory in new_directories:
                shared_directories.add(directory)
            config.shared_directories = list(shared_directories)
        else:
            replace = Confirm.ask(
                "Are you sure you want to overwrite the shared directories?"
            )
            if replace:
                config.shared_directories = new_directories
                print("Shared directories overwritten.")
        write_config(config=config)
    else:
        shared_directoires = get_shared_directories()
        print(shared_directoires)


@config_app.command()
def pickle_file(
    new_pickle_file: str = Argument(
        None, help="New path to beets pickle file to replace the existing value."
    ),
):
    """Show pickle file value."""
    if new_pickle_file:
        config = get_config()
        replace = Confirm.ask("Are you sure you want to overwrite the pickle file?")
        if replace:
            config.pickle_file = new_pickle_file
            print("Pickle file overwritten.")
        write_config(config=config)
    else:
        pickle_file = get_pickle_file()
        print(pickle_file)


@config_app.command()
def ignored_directories(
    new_directories: list[str] = Argument(
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
    if new_directories:
        config = get_config()
        if add:
            new_ignored_directories = set(config.ignored_directories)
            for directory in new_directories:
                new_ignored_directories.add(directory)
            config.ignored_directories = list(new_ignored_directories)
        else:
            replace = Confirm.ask(
                "Are you sure you want to overwrite the ignored directories?"
            )
            if replace:
                config.ignored_directories = new_directories
                print("Ignored directories overwritten.")
        write_config(config=config)
    else:
        ignored_directories = get_ignored_directories()
        print(ignored_directories)


@config_app.command()
def music_player(
    new_music_player: str = Argument(
        None, help="New default music player to replace the existing value."
    ),
):
    """Show music player value."""
    if new_music_player:
        config = get_config()
        replace = Confirm.ask("Are you sure you want to overwrite the music player?")
        if replace:
            config.music_player = new_music_player
            print("Muisc player overwritten.")
        write_config(config=config)
    else:
        music_player = get_music_player()
        print(music_player)
