from pytest import mark
from test_config import config_command, get_import_values

from tests.conftest import get_command_output, get_help_args
from tsundeoku import main


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_import_help(arg, mock_get_argv, monkeypatch):
    config_help_text = 'Show and set default values for "import" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output(["config", "import", arg])
    assert config_help_text in output


def test_config_import():
    output = get_command_output([config_command, "import"])
    assert output == get_import_values()
