from pytest import mark

from tests.conftest import call_command
from tsundeoku import __version__

version = "0.5.0"


def test_version():
    assert __version__ == version


@mark.parametrize("arg", ["--version", "-V"])
def test_version_display(arg: str):
    version_display = f"tsundeoku {version}\n"
    output = call_command([arg])
    assert output == version_display


@mark.parametrize("arg", [None, "--help", "-h"])
def test_help(arg: str):
    app_name_definition = '積んでおく("tsundeoku"): "to pile up for later"'
    help_text = "Import audio files from a shared folder to a local library."
    output = call_command([arg])
    assert app_name_definition in output
    assert help_text in output
