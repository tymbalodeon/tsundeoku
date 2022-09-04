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
from rich import print
from rich.markup import escape
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


class NotificationsConfig(BaseModel):
    username = ""
    password = ""
    email_on = False
    system_on = False


class Config(BaseModel):
    file_system = FileSystemConfig()
    import_new = ImportConfig()
    reformat = ReformatConfig()
    notifications = NotificationsConfig()


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


def get_file_system_config() -> FileSystemConfig:
    config = get_loaded_config()
    return config.file_system


def get_shared_directories() -> set[Path]:
    file_system = get_file_system_config()
    return file_system.shared_directories


def get_pickle_file() -> Path:
    file_system = get_file_system_config()
    return file_system.pickle_file


def get_ignored_directories() -> set[Path]:
    file_system = get_file_system_config()
    return file_system.ignored_directories


def get_music_player() -> str:
    file_system = get_file_system_config()
    return file_system.music_player


def update_config_key(config: dict, old_value: str, new_value: str) -> dict:
    return {
        new_value if key == old_value else key: value for key, value in config.items()
    }


def convert_import_new_to_import(config: dict) -> dict:
    return update_config_key(config, "import_new", "import")


def convert_import_to_import_new(config: dict) -> dict:
    return update_config_key(config, "import", "import_new")


def as_toml(config: Config) -> dict:
    config_toml: dict = config.dict()
    file_system = config_toml["file_system"]
    for key, value in file_system.items():
        if isinstance(value, set):
            file_system[key] = [path.as_posix() for path in value]
        elif isinstance(value, Path):
            file_system[key] = value.as_posix()
    config_toml = convert_import_new_to_import(config_toml)
    return config_toml


def print_errors(validation_error: ValidationError, level: StyleLevel):
    for error in validation_error.errors():
        message = f"{level.name}: {error['msg']}"
        print_with_theme(message, level=level)
    print()


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
    elif not is_valid_config(config):
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
    config_values = convert_import_to_import_new(config_values)
    return Config(**config_values)


def print_config_section(config: BaseModel | dict):
    if isinstance(config, BaseModel):
        section = config.dict()
    else:
        section = config
    for key, value in section.items():
        if isinstance(value, set):
            value = {path.as_posix() for path in value} or None
        elif key == "password" and value:
            value = "********"
        print(f"{key}={value}")


def print_config_values():
    config = get_loaded_config()
    first_item = True
    for section, values in config.dict().items():
        if not first_item:
            print()
        section = escape(f"[{section}]")
        print(section)
        print_config_section(values)
        first_item = False
