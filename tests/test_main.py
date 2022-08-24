from typer.testing import CliRunner

from musicbros import __version__
from musicbros.main import app


def test_version():
    expected_version = "0.3.0"
    expected_version_display = f"musicbros {expected_version}\n"
    assert __version__ == expected_version
    for option in ["--version", "-V"]:
        result = CliRunner().invoke(app, option)
        assert result.stdout == expected_version_display
        assert result.exit_code == 0


def test_help():
    app_description = (
        'CLI for managing imports from a shared folder to a "beets" library'
    )
    for option in ["--help", "-h"]:
        result = CliRunner().invoke(app, option)
        assert app_description in result.stdout
        assert result.exit_code == 0
