from typer.testing import CliRunner

from tsundeoku import __version__
from tsundeoku.main import tsundeoku


def test_version():
    expected_version = "0.4.0"
    expected_version_display = f"tsundeoku {expected_version}\n"
    assert __version__ == expected_version
    for option in ["--version", "-v"]:
        result = CliRunner().invoke(tsundeoku, option)
        assert result.output == expected_version_display
        assert result.exit_code == 0


def test_help():
    app_description = (
        "CLI for importing audio files from a shared folder to a local library"
    )
    for option in ["--help", "-h"]:
        result = CliRunner().invoke(tsundeoku, option)
        assert app_description in result.output
        assert result.exit_code == 0
