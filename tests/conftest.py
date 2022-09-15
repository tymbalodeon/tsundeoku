from collections.abc import Callable
from pathlib import Path

from pytest import fixture
from typer.testing import CliRunner

from tsundeoku.config import config
from tsundeoku.config.config import (
    Config,
    FileSystemConfig,
    get_default_music_player,
    get_default_pickle_file,
    get_default_shared_directories,
)
from tsundeoku.main import tsundeoku


@fixture(autouse=True)
def set_mock_home(monkeypatch, tmp_path_factory):
    home = tmp_path_factory.mktemp("home")

    def mock_home():
        return home

    def mock_get_default_config():
        default_shared_directories = get_default_shared_directories()
        default_pickle_file = get_default_pickle_file()
        default_music_player = get_default_music_player()
        pickle_parent = default_pickle_file.parent
        paths = list(default_shared_directories) + [pickle_parent]
        for path in paths:
            if not path.exists():
                Path.mkdir(path, parents=True)
        default_pickle_file.touch()
        file_system = FileSystemConfig(
            shared_directories=default_shared_directories,
            pickle_file=default_pickle_file,
            music_player=default_music_player,
        )
        return Config(**{"file_system": file_system})

    monkeypatch.setattr(Path, "home", mock_home)
    monkeypatch.setattr(config, "get_default_config", mock_get_default_config)


mock_argv = Callable[[], list[str]]


def get_mock_get_argvs() -> tuple[mock_argv, mock_argv]:
    def mock_get_argv_long() -> list[str]:
        return ["--help"]

    def mock_get_argv_short() -> list[str]:
        return ["-h"]

    return mock_get_argv_long, mock_get_argv_short


def get_help_args() -> list[tuple[str, mock_argv]]:
    mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs()
    return [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]


def call_command(args: list[str]):
    if not any(args):
        return CliRunner().invoke(tsundeoku)
    return CliRunner().invoke(tsundeoku, args)


def get_command_output(args: list[str]) -> str:
    return call_command(args).output


def strip_newlines(text: str) -> str:
    return text.replace("\n", "")
