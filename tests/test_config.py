from pytest import mark
from typer.testing import CliRunner

from tsundeoku import main
from tsundeoku.main import tsundeoku

config_help_text = "Show [default] and set config values."


def mock_get_argv_long():
    return ["config", "--help"]


def mock_get_argv_short():
    return ["config", "-h"]


@mark.parametrize(
    "arg, mock_get_argv", [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]
)
def test_config_help(arg, mock_get_argv, monkeypatch):
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    result = CliRunner().invoke(tsundeoku, ["config", arg])
    assert config_help_text in result.output
