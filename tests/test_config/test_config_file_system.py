from pytest import mark

from tests.conftest import get_help_args, get_output
from tsundeoku import main
from test_config import config_command, file_system_values


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_file_system_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show and set values for the file-system."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output(["config", "file-system", arg])
    assert config_help_text in output


def test_config_file_system():
    output = get_output([config_command, "file-system"])
    assert output == file_system_values
