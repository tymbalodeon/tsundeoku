from collections import namedtuple
from pathlib import Path

from pytest import MonkeyPatch, TempPathFactory, fixture, mark

from tsundeoku import main, schedule
from tsundeoku.schedule import (
    get_plist_path,
    get_tmp_path,
    launchctl,
    load_plist,
    stamp_logs,
)

from .conftest import MockArgV, call_command, get_help_args

schedule_command = "schedule"


@fixture(autouse=True)
def set_mock_get_tmp_path(
    monkeypatch: MonkeyPatch, tmp_path_factory: TempPathFactory
):
    tmp = tmp_path_factory.mktemp("tmp")

    def mock_get_tmp_path() -> Path:
        return tmp

    def mock_launchctl(command: str, path: Path | None = None) -> bytes:
        return b"tsundeoku"

    monkeypatch.setattr(schedule, "get_tmp_path", mock_get_tmp_path)
    monkeypatch.setattr(schedule, "launchctl", mock_launchctl)
    launch_agents = Path.home() / "Library/LaunchAgents"
    Path.mkdir(launch_agents, parents=True)


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_help(
    arg: str, mock_get_argv: MockArgV, monkeypatch: MonkeyPatch
):
    config_help_text = "Schedule import command to run automatically."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = call_command([schedule_command, arg])
    assert config_help_text in output


def set_mock_is_currently_scheduled(
    monkeypatch: MonkeyPatch, is_currently_scheduled=True
):
    def mock_is_currently_scheduled() -> bool:
        return is_currently_scheduled

    monkeypatch.setattr(
        schedule, "is_currently_scheduled", mock_is_currently_scheduled
    )


not_scheduled_message = "Import is not currently scheduled.\n"
error_message = "Error retrieving schedule information.\n"


def test_schedule_not_scheduled(monkeypatch: MonkeyPatch):
    set_mock_is_currently_scheduled(monkeypatch, is_currently_scheduled=False)
    output = call_command([schedule_command])
    expected_output = not_scheduled_message
    assert output == expected_output


def test_schedule_scheduled_no_file(monkeypatch: MonkeyPatch):
    set_mock_is_currently_scheduled(monkeypatch)
    output = call_command([schedule_command])
    expected_output = error_message
    assert output == expected_output


def test_schedule_scheduled_file_daily(monkeypatch: MonkeyPatch):
    set_mock_is_currently_scheduled(monkeypatch)
    load_plist(9, 0)
    output = call_command([schedule_command])
    expected_output = (
        "Import is currently scheduled for every day at 09:00AM.\n"
    )
    assert output == expected_output


def test_schedule_scheduled_file_hourly(monkeypatch: MonkeyPatch):
    set_mock_is_currently_scheduled(monkeypatch)
    load_plist(None, 30)
    output = call_command([schedule_command])
    expected_output = (
        "Import is currently scheduled for every hour at **:30 minutes.\n"
    )
    assert output == expected_output


def test_schedule_scheduled_empty_file(monkeypatch: MonkeyPatch):
    set_mock_is_currently_scheduled(monkeypatch)
    plist_path = get_plist_path()
    plist_path.touch()
    output = call_command([schedule_command])
    assert output == error_message


def test_schedule_scheduled_bad_file(monkeypatch: MonkeyPatch):
    set_mock_is_currently_scheduled(monkeypatch)
    plist_path = get_plist_path()
    plist_path.write_text("<Label>BadValue</Label>")
    output = call_command([schedule_command])
    assert output == error_message


def test_schedule_on_daily():
    output = call_command([schedule_command, "--on", "9:00am"])
    assert output == "Scheduled import for every day at 09:00AM.\n"


def test_schedule_on_hourly():
    output = call_command([schedule_command, "--on", "**:30"])
    assert output == "Scheduled import for every hour at **:30 minutes.\n"


def test_schedule_off():
    call_command([schedule_command, "--on", "9:00am"])
    output = call_command([schedule_command, "--off"])
    assert output == "Turned off scheduled import.\n"
    output = call_command([schedule_command])
    assert output == not_scheduled_message


def test_schedule_logs():
    time = stamp_logs()
    output = call_command([schedule_command, "--logs"])
    assert time in output


def test_get_tmp_path():
    tmp_path = get_tmp_path()
    assert tmp_path == Path("/tmp")


def test_launchctl_no_path(monkeypatch: MonkeyPatch):
    def mock_run(args: list[Path | str], capture_output: bool):
        Stdout = namedtuple("Stdout", "stdout")
        output = str.encode(f"args: {args}, capture_output: {capture_output}")
        return Stdout(output)

    monkeypatch.setattr(schedule, "run", mock_run)
    output = launchctl("load")
    expected_output = b"args: ['launchctl', 'load'], capture_output: True"
    assert output == expected_output


def test_launchctl_path(monkeypatch: MonkeyPatch):
    def mock_run(args: list[Path | str], capture_output: bool):
        Stdout = namedtuple("Stdout", "stdout")
        output = str.encode(f"args: {args}, capture_output: {capture_output}")
        return Stdout(output)

    monkeypatch.setattr(schedule, "run", mock_run)
    output = launchctl("load", path=Path("path"))
    expected_output = (
        b"args: ['launchctl', 'load', PosixPath('path')], capture_output: True"
    )
    assert output == expected_output
