from pathlib import Path

from pytest import mark

from tests.conftest import get_help_args, get_output
from tsundeoku import main

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
    output = get_output([config_command, arg])
    assert config_help_text in output


def test_config():
    output = get_output([config_command])
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
    output = get_output([config_command, "--path"])
    home = str(Path.home())
    assert home in output.replace("\n", "")


def test_config_path_includes_config_path():
    output = get_output([config_command, "--path"])
    assert ".config/tsundeoku/tsundeoku.toml" in output
