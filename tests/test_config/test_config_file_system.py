from pytest import mark
from test_config import config_command, get_file_system_values

from tests.conftest import get_command_output, get_help_args, strip_newlines
from tsundeoku import main


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_file_system_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show and set values for the file-system."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output(["config", "file-system", arg])
    assert config_help_text in output


def test_config_file_system():
    output = get_command_output([config_command, "file-system"])
    values = get_file_system_values()
    output = strip_newlines(output)
    values = strip_newlines(values)
    assert output == values
