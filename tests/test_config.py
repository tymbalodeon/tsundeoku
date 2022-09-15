from pytest import mark

from tsundeoku import main

from .conftest import get_mock_get_argvs, get_output

config_command = "config"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs()
args = [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]
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


@mark.parametrize("arg, mock_get_argv", args)
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show [default] and set config values."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, arg])
    assert config_help_text in output


@mark.parametrize("arg, mock_get_argv", args)
def test_config_file_system_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show and set values for the file-system."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, "file-system", arg])
    assert config_help_text in output


@mark.parametrize("arg, mock_get_argv", args)
def test_config_import_help(arg, mock_get_argv, monkeypatch):
    config_help_text = 'Show and set default values for "import" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, "import", arg])
    assert config_help_text in output


@mark.parametrize("arg, mock_get_argv", args)
def test_config_notifications_help(arg, mock_get_argv, monkeypatch):
    config_help_text = (
        "Show and set values for notifications from scheduled import command."
    )
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, "notifications", arg])
    assert config_help_text in output


@mark.parametrize("arg, mock_get_argv", args)
def test_config_reformat_help(arg, mock_get_argv, monkeypatch):
    config_help_text = 'Show and set default values for "reformat" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, "reformat", arg])
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


def test_config_file_system():
    output = get_output([config_command, "file-system"])
    assert output == file_system_values


def test_config_import():
    output = get_output([config_command, "import"])
    assert output == import_values


def test_config_reformat():
    output = get_output([config_command, "reformat"])
    assert output == reformat_values


def test_config_notifications():
    output = get_output([config_command, "notifications"])
    assert output == notifications_values
