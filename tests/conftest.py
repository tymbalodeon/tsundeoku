from collections.abc import Callable
from pathlib import Path

from pytest import fixture
from typer.testing import CliRunner

from tsundeoku.main import tsundeoku

mock_argv = Callable[[], list[str]]


def get_mock_get_argvs() -> tuple[mock_argv, mock_argv]:
    def mock_get_argv_long() -> list[str]:
        return ["--help"]

    def mock_get_argv_short() -> list[str]:
        return ["-h"]

    return mock_get_argv_long, mock_get_argv_short


@fixture(autouse=True)
def set_mock_home(monkeypatch, tmp_path_factory):
    home = tmp_path_factory.mktemp("home")

    def mock_home():
        return home

    monkeypatch.setattr(Path, "home", mock_home)


def get_output(commands: list[str]) -> str:
    if not any(commands):
        return CliRunner().invoke(tsundeoku).output
    return CliRunner().invoke(tsundeoku, commands).output
