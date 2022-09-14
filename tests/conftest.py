from collections.abc import Callable
from pathlib import Path

from pytest import fixture

mock_argv = Callable[[], list[str]]


def get_mock_get_argv(command: str, short=False) -> mock_argv:
    if short:
        help_option = "-h"
    else:
        help_option = "--help"

    def mock_get_argv() -> list[str]:
        return [command, help_option]

    return mock_get_argv


def get_mock_get_argvs(command: str) -> tuple[mock_argv, mock_argv]:
    mock_get_argv_long = get_mock_get_argv(command)
    mock_get_argv_short = get_mock_get_argv(command, short=True)
    return mock_get_argv_long, mock_get_argv_short


@fixture(autouse=True)
def set_mock_home(monkeypatch, tmp_path_factory):
    def mock_home():
        home = tmp_path_factory.mktemp("home")
        return home

    monkeypatch.setattr(Path, "home", mock_home)
