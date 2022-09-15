from pytest import mark

from tsundeoku import main

from .conftest import get_mock_get_argvs, get_output

config_command = "schedule"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs()


@mark.parametrize(
    "arg, mock_get_argv", [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]
)
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Schedule import command to run automatically."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, arg])
    assert config_help_text in output
