from pytest import mark

from tests.conftest import get_help_args, get_output
from tsundeoku import main
from test_config import config_command, import_values


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_import_help(arg, mock_get_argv, monkeypatch):
    config_help_text = 'Show and set default values for "import" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output(["config", "import", arg])
    assert config_help_text in output


def test_config_import():
    output = get_output([config_command, "import"])
    assert output == import_values
