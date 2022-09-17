from pathlib import Path

from pytest import fixture, mark

from tsundeoku import main, schedule
from tsundeoku.schedule import stamp_logs

from .conftest import get_command_output, get_help_args

schedule_command = "schedule"


@fixture(autouse=True)
def set_mock_get_tmp_path(monkeypatch, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("tmp")

    def mock_get_tmp_path() -> Path:
        return tmp

    monkeypatch.setattr(schedule, "get_tmp_path", mock_get_tmp_path)


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Schedule import command to run automatically."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([schedule_command, arg])
    assert config_help_text in output


def test_schedule_not_scheduled(monkeypatch):
    def mock_is_currently_scheduled() -> bool:
        return False

    monkeypatch.setattr(schedule, "is_currently_scheduled", mock_is_currently_scheduled)
    output = get_command_output([schedule_command])
    expected_output = "Import is not currently scheduled.\n"
    assert output == expected_output


def test_schedule_logs():
    time = stamp_logs()
    output = get_command_output([schedule_command, "--logs"])
    assert time in output
