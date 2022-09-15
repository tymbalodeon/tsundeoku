from pytest import mark
from test_config import config_command, reformat_values

from tests.conftest import get_help_args, get_output
from tsundeoku import main


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_reformat_help(arg, mock_get_argv, monkeypatch):
    config_help_text = 'Show and set default values for "reformat" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_output([config_command, "reformat", arg])
    assert config_help_text in output


def test_config_reformat():
    output = get_output([config_command, "reformat"])
    assert output == reformat_values
