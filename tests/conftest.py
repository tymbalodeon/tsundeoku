from collections.abc import Callable
from pathlib import Path

from pytest import fixture
from typer.testing import CliRunner

from tsundeoku.main import tsundeoku


@fixture(autouse=True)
def set_mock_home(monkeypatch, tmp_path_factory):
    home = tmp_path_factory.mktemp("home")

    def mock_home():
        return home

    monkeypatch.setattr(Path, "home", mock_home)


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
