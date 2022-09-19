from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, DirectoryPath, Field, FilePath, validator
from pytest import MonkeyPatch, TempPathFactory, fixture
from typer.testing import CliRunner

from tsundeoku import reformat
from tsundeoku.config import config
from tsundeoku.config.config import (
    ImportConfig,
    NotificationsConfig,
    ReformatConfig,
    get_default_music_player,
    get_default_pickle_file,
    get_default_shared_directories,
    write_config_values,
)
from tsundeoku.main import tsundeoku


class MockFileSystemConfig(BaseModel):
    shared_directories: set[DirectoryPath] = Field(
        default_factory=get_default_shared_directories
    )
    pickle_file: FilePath = Field(default_factory=get_default_pickle_file)
    ignored_directories: set[DirectoryPath] = Field(default_factory=list)
    music_player: str = get_default_music_player()

    @validator("shared_directories", "ignored_directories")
    def validate_directory_paths(cls, paths: list[str]) -> set[Path]:
        return {Path(path).expanduser() for path in paths}

    @validator("pickle_file")
    def validate_file_path(cls, path: str) -> Path:
        return Path(path)

    @validator("music_player")
    def validate_application(cls, application_name: str) -> str:
        default_music_player = get_default_music_player()
        if application_name in (default_music_player, "Custom"):
            return application_name
        raise ValueError(f'application "{application_name}" not found')


class MockConfig(BaseModel):
    file_system = MockFileSystemConfig()
    import_new = ImportConfig()
    reformat = ReformatConfig()
    notifications = NotificationsConfig()


class MockLibrary:
    def albums(self, query: str) -> list[str]:
        return []

    def items(self, query: str) -> list[str]:
        return []


@fixture(autouse=True)
def set_mock_home(monkeypatch: MonkeyPatch, tmp_path_factory: TempPathFactory):
    home = tmp_path_factory.mktemp("home")

    def mock_home() -> Path:
        return home

    def mock_get_config_instance(config_values: dict | None = None) -> MockConfig:
        if config_values:
            return MockConfig(**config_values)
        default_shared_directories = get_default_shared_directories()
        default_pickle_file = get_default_pickle_file()
        default_music_player = get_default_music_player()
        pickle_parent = default_pickle_file.parent
        paths = list(default_shared_directories) + [pickle_parent]
        for path in paths:
            if not path.exists():
                Path.mkdir(path, parents=True)
        default_pickle_file.touch()
        file_system = MockFileSystemConfig(
            shared_directories=default_shared_directories,
            pickle_file=default_pickle_file,
            music_player=default_music_player,
        )
        return MockConfig(**{"file_system": file_system})

    def mock_get_library() -> MockLibrary:
        return MockLibrary()

    monkeypatch.setattr(Path, "home", mock_home)
    monkeypatch.setattr(config, "get_config_instance", mock_get_config_instance)
    monkeypatch.setattr(reformat, "get_library", mock_get_library)
    write_config_values()


MockArgV = Callable[[], list[str]]


def get_mock_get_argvs() -> tuple[MockArgV, MockArgV]:
    def mock_get_argv_long() -> list[str]:
        return ["--help"]

    def mock_get_argv_short() -> list[str]:
        return ["-h"]

    return mock_get_argv_long, mock_get_argv_short


def get_help_args() -> list[tuple[str, MockArgV]]:
    mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs()
    return [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]


def call_command(args: list[str]) -> str:
    if not any(args):
        return CliRunner().invoke(tsundeoku).output
    return CliRunner().invoke(tsundeoku, args).output


def strip_newlines(text: str) -> str:
    return text.replace("\n", "")
