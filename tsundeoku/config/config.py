from enum import Enum
from pathlib import Path
from subprocess import run

from pydantic import BaseModel, DirectoryPath, Field, FilePath, validator
from rich.console import Console
from rich.style import Style
from rich.syntax import Syntax
from rich.theme import Theme
from tomli import loads
from tomli_w import dumps

APP_NAME = "tsundeoku"
THEME_NAME = "theme"
CONFIG_PATH = f".config/{APP_NAME}"


def get_default_shared_directories() -> set[Path]:
    default_shared_directory = Path.home() / "Dropbox"
    return {default_shared_directory}


def get_default_pickle_file() -> Path:
    return Path.home() / ".config/beets/state.pickle"


class Config(BaseModel):
    shared_directories: set[DirectoryPath] = Field(
        default_factory=get_default_shared_directories
    )
    pickle_file: FilePath = Field(default_factory=get_default_pickle_file)
    ignored_directories: set[DirectoryPath] = Field(default_factory=list)
    music_player = "Swinsian"

    @validator("shared_directories", "ignored_directories")
    def validate_directory_paths(cls, paths: list[str]) -> set[Path]:
        return {Path(path) for path in paths}

    @validator("pickle_file")
    def validate_file_path(cls, path: str) -> Path:
        return Path(path)

    @validator("music_player")
    def validate_application(cls, application_name: str) -> str:
        command = f'mdfind "kMDItemKind == \'Application\'" | grep "{application_name}"'
        application_exists = run(command, shell=True, capture_output=True).stdout
        if not application_exists:
            raise ValueError(f'application "{application_name}" not found')
        return application_name


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


def as_toml(config: dict) -> dict:
    for key, value in config.items():
        if isinstance(value, set):
            config[key] = [path.as_posix() for path in value]
        elif isinstance(value, Path):
            config[key] = value.as_posix()
    return config


def write_config_values(**config_and_theme: Config | ThemeConfig):
    if "config" not in config_and_theme:
        config = Config()
    else:
        config = config_and_theme["config"]
    if "theme" not in config_and_theme:
        theme = ThemeConfig()
    else:
        theme = config_and_theme["theme"]
    config_values = as_toml(config.dict())
    theme_values = as_toml(theme.dict())
    complete_config = {APP_NAME: config_values, THEME_NAME: theme_values}
    config_file = get_config_path()
    config_file.write_text(dumps(complete_config))


def get_config_file() -> Path:
    config_file = get_config_path()
    if not config_file.is_file():
        write_config_values()
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


class StyleLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def get_theme() -> Theme:
    theme_config_values = read_theme_config_values()
    return Theme(theme_config_values)


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


def get_theme_config() -> ThemeConfig:
    theme_config_values = read_theme_config_values()
    return ThemeConfig(**theme_config_values)


def print_config_values():
    config_file = str(get_config_file())
    syntax = Syntax.from_path(config_file, lexer="toml", theme="ansi_dark")
    print_with_theme(syntax)
