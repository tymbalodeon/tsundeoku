from pytest import mark
from typer.testing import CliRunner

from tsundeoku import __version__
from tsundeoku.main import tsundeoku

version = "0.4.0"


def test_version():
    assert __version__ == version


version_display = f"tsundeoku {version}\n"


@mark.parametrize(
    "arg, version", [("--version", version_display), ("-V", version_display)]
)
def test_version_display(arg, version):
    result = CliRunner().invoke(tsundeoku, arg)
    assert result.output == version


app_help_text = "CLI for importing audio files from a shared folder to a local library"


@mark.parametrize(
    "arg, app_description",
    [(None, app_help_text), ("--help", app_help_text), ("-h", app_help_text)],
)
def test_help(arg, app_description):
    result = CliRunner().invoke(tsundeoku, arg)
    assert app_description in result.output
