from typer.testing import CliRunner

from musicbros import __version__
from musicbros.main import app

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
    config_help = "Create, update, and display config values"
    result = CLI_RUNNER.invoke(app, ["config", "-h"])
    assert config_help in result.stdout
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
