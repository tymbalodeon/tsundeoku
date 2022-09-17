from pytest import mark

from tests.conftest import get_command_output
from tsundeoku import __version__

version = "0.4.0"


def test_version():
    assert __version__ == version


@mark.parametrize("arg", ["--version", "-V"])
def test_version_display(arg):
    version_display = f"tsundeoku {version}\n"
    output = get_command_output([arg])
    assert output == version_display


@mark.parametrize("arg", [None, "--help", "-h"])
def test_help(arg):
    help_text = "CLI for importing audio files from a shared folder to a local library"
    output = get_command_output([arg])
    assert help_text in output
