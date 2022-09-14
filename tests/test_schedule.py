from pytest import mark
from typer.testing import CliRunner

from tsundeoku import main
from tsundeoku.main import tsundeoku

from .conftest import get_mock_get_argvs

config_command = "schedule"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs(config_command)


@mark.parametrize(
    "arg, mock_get_argv", [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]
)
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Schedule import command to run automatically."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = CliRunner().invoke(tsundeoku, [config_command, arg]).output
    assert config_help_text in output
