from typer.testing import CliRunner

from musicbros import __version__
from musicbros.main import app
from musicbros.style import format_int_with_commas

EXPECTED_VERSION = "0.3.0"
CLI_RUNNER = CliRunner()


def test_version():
    assert __version__ == EXPECTED_VERSION
    for option in ["--version", "-V"]:
        result = CLI_RUNNER.invoke(app, [option])
        assert result.exit_code == 0
        assert result.stdout == f"musicbros {EXPECTED_VERSION}\n"


def test_help():
    app_description = (
        'CLI for managing imports from a shared folder to a "beets" library'
    )
    for option in ["--help", "-h"]:
        result = CLI_RUNNER.invoke(app, [option])
        assert app_description in result.stdout
        assert result.exit_code == 0


def test_config_help():
    config_help_text = "Create, update, and display config values"
    result = CLI_RUNNER.invoke(app, ["config", "-h"])
    assert config_help_text in result.stdout
    assert result.exit_code == 0


def test_config():
    result = CLI_RUNNER.invoke(app, ["config"])
    stdout = result.stdout
    section = "[musicbros]"
    assert section in stdout
    options = ["shared_directory", "pickle_file", "ignored_directories", "music_player"]
    for option in options:
        option = f"{option} = "
        assert option in stdout
    assert result.exit_code == 0


def test_style_int():
    one_thousand = 1000
    one_thousand_with_comma = format_int_with_commas(one_thousand)
    assert one_thousand_with_comma == "1,000"
