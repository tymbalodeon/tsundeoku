from pytest import mark

from tests.conftest import get_output
from tsundeoku import __version__

version = "0.4.0"


def test_version():
    assert __version__ == version


version_display = f"tsundeoku {version}\n"


@mark.parametrize(
    "arg, version", [("--version", version_display), ("-V", version_display)]
)
def test_version_display(arg, version):
    output = get_output([arg])
    assert output == version


@mark.parametrize("arg", [None, "--help", "-h"])
def test_help(arg):
    help_text = "CLI for importing audio files from a shared folder to a local library"
    output = get_output([arg])
    assert help_text in output
