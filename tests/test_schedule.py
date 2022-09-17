from pytest import mark

from tsundeoku import main

from .conftest import get_command_output, get_help_args

config_command = "schedule"


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Schedule import command to run automatically."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([config_command, arg])
    assert config_help_text in output
