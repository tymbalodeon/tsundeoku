from pytest import mark
from test_config import config_command, notifications_values

from tests.conftest import get_command_output, get_help_args
from tsundeoku import main


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_notifications_help(arg, mock_get_argv, monkeypatch):
    config_help_text = (
        "Show and set values for notifications from scheduled import command."
    )
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([config_command, "notifications", arg])
    assert config_help_text in output


def test_config_notifications():
    output = get_command_output([config_command, "notifications"])
    assert output == notifications_values
