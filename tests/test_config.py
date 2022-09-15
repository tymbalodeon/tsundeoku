from pytest import mark
from typer.testing import CliRunner

from tsundeoku import main
from tsundeoku.main import tsundeoku

from .conftest import get_mock_get_argvs

config_command = "config"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs(config_command)


@mark.parametrize(
    "arg, mock_get_argv", [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]
)
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show [default] and set config values."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = CliRunner().invoke(tsundeoku, [config_command, arg]).output
    assert config_help_text in output


def test_config():
    output = CliRunner().invoke(tsundeoku, config_command).output
    expected_config_display = (
        "[file_system]\n"
        "shared_directories={'/Users/rrosen/Dropbox'}\n"
        "pickle_file=/Users/rrosen/.config/beets/state.pickle\n"
        "ignored_directories=None\n"
        "music_player=Swinsian\n"
        "\n"
        "[import]\n"
        "reformat=True\n"
        "ask_before_disc_update=False\n"
        "ask_before_artist_update=False\n"
        "allow_prompt=True\n"
        "\n"
        "[reformat]\n"
        "remove_bracket_years=True\n"
        "remove_bracket_instruments=True\n"
        "expand_abbreviations=True\n"
        "\n"
        "[notifications]\n"
        "system_on=False\n"
        "email_on=False\n"
        "username=\n"
        "password=\n"
    )
    assert output == expected_config_display
