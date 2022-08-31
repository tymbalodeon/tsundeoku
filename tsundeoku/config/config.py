from pathlib import Path
from subprocess import run
from typing import cast

from pydantic import (
    BaseModel,
    DirectoryPath,
    Field,
    FilePath,
    ValidationError,
    validator,
)
from rich.syntax import Syntax
from tomli import loads
from tomli_w import dumps

from tsundeoku.style import StyleLevel, print_with_theme


def get_default_shared_directories() -> set[Path]:
    default_shared_directory = Path.home() / "Dropbox"
    return {default_shared_directory}


def get_default_pickle_file() -> Path:
    return Path.home() / ".config/beets/state.pickle"


class FileSystemConfig(BaseModel):
    shared_directories: set[DirectoryPath] = Field(
        default_factory=get_default_shared_directories
    )
    pickle_file: FilePath = Field(default_factory=get_default_pickle_file)
    ignored_directories: set[DirectoryPath] = Field(default_factory=list)
    music_player = "Swinsian"

    @validator("shared_directories", "ignored_directories")
    def validate_directory_paths(cls, paths: list[str]) -> set[Path]:
        return {Path(path).expanduser() for path in paths}

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


class ImportConfig(BaseModel):
    reformat = True
    ask_before_disc_update = False
    ask_before_artist_update = False
    allow_prompt = True


class ReformatConfig(BaseModel):
    remove_bracket_years = True
    remove_bracket_instruments = True
    expand_abbreviations = True


class Config(BaseModel):
    file_system = FileSystemConfig()
    import_new = ImportConfig()
    reformat = ReformatConfig()


STATE = {"config": Config()}
APP_NAME = "tsundeoku"
CONFIG_PATH = f".config/{APP_NAME}"


def get_config_path() -> Path:
    config_directory = Path.home() / CONFIG_PATH
    if not config_directory.exists():
        Path.mkdir(config_directory, parents=True)
    return config_directory / f"{APP_NAME}.toml"


def get_loaded_config() -> Config:
    return cast(Config, STATE["config"])


def rename_import_config(config: dict) -> dict:
    return {
        "import" if key == "import_new" else key: value for key, value in config.items()
    }


def as_toml(config: Config) -> dict:
    config_toml: dict = config.dict()
    file_system = config_toml["file_system"]
    for key, value in file_system.items():
        if isinstance(value, set):
            file_system[key] = [path.as_posix() for path in value]
        elif isinstance(value, Path):
            file_system[key] = value.as_posix()
    config_toml = rename_import_config(config_toml)
    return config_toml


def print_errors(validation_error: ValidationError, level: StyleLevel):
    for error in validation_error.errors():
        message = f"{level.name}: {error['msg']}"
        print_with_theme(message, level=level)


def is_valid_config(config_values: Config) -> bool:
    try:
        Config(**config_values.dict())
        return True
    except ValidationError as error:
        print_errors(error, level=StyleLevel.ERROR)
        return False


class InvalidConfig(Exception):
    pass


def write_config_values(config: Config | None = None):
    if not config:
        config = Config()
    if not is_valid_config(config):
        raise InvalidConfig()
    config_toml = as_toml(config)
    config_file = get_config_path()
    config_file.write_text(dumps(config_toml))


def get_config_file() -> Path:
    config_file = get_config_path()
    if not config_file.is_file():
        write_config_values()
    return config_file


def get_config() -> Config:
    config_file = get_config_file()
    config_text = config_file.read_text()
    config_values = loads(config_text)
    return Config(**config_values)


def print_config_values():
    config_file = str(get_config_file())
    syntax = Syntax.from_path(config_file, lexer="toml", theme="ansi_dark")
    print_with_theme(syntax)
