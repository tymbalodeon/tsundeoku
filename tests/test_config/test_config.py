from pathlib import Path

from pytest import mark

from tests.conftest import call_command, get_command_output, get_help_args
from tsundeoku import main
from tsundeoku.config import main as config_main
from tsundeoku.config.config import get_config_path

config_command = "config"
file_system_values = (
    "shared_directories={'/Users/rrosen/Dropbox'}\n"
    "pickle_file=/Users/rrosen/.config/beets/state.pickle\n"
    "ignored_directories=None\n"
    "music_player=Swinsian\n"
)
import_values = (
    "reformat=True\n"
    "ask_before_disc_update=False\n"
    "ask_before_artist_update=False\n"
    "allow_prompt=True\n"
)
notifications_values = "system_on=False\nemail_on=False\nusername=\npassword=\n"
reformat_values = (
    "remove_bracket_years=True\n"
    "remove_bracket_instruments=True\n"
    "expand_abbreviations=True\n"
)


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show [default] and set config values."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([config_command, arg])
    assert config_help_text in output


def test_config():
    output = get_command_output([config_command])
    expected_config_display = (
        "[file_system]\n"
        f"{file_system_values}"
        "\n"
        "[import]\n"
        f"{import_values}"
        "\n"
        "[reformat]\n"
        f"{reformat_values}"
        "\n"
        "[notifications]\n"
        f"{notifications_values}"
    )
    assert output == expected_config_display


def test_config_path_includes_home():
    output = get_command_output([config_command, "--path"])
    home = str(Path.home())
    assert home in output.replace("\n", "")


def test_config_path_includes_config_path():
    output = get_command_output([config_command, "--path"])
    assert ".config/tsundeoku/tsundeoku.toml" in output


def test_config_file(monkeypatch, mocker):
    def mock_launch(url: str, locate: bool):
        pass

    monkeypatch.setattr(config_main, "launch", mock_launch)
    spy = mocker.spy(config_main, "launch")
    call_command([config_command, "--file"])
    config_path = str(get_config_path())
    spy.assert_called_once_with(config_path, locate=True)


def test_config_edit(monkeypatch, mocker):
    def mock_run(args: list[str]):
        pass

    monkeypatch.setattr(config_main, "run", mock_run)
    monkeypatch.setattr(config_main, "environ", {})
    spy = mocker.spy(config_main, "run")
    call_command([config_command, "--edit"])
    config_path = get_config_path()
    spy.assert_called_once_with(["vim", config_path])


def test_config_reset_all():
    pass


def test_config_reset_commands():
    pass
