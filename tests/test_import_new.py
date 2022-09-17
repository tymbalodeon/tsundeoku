from pytest import mark

from tsundeoku import main

from .conftest import get_command_output, get_help_args

import_command = "import"


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_import_help(arg, mock_get_argv, monkeypatch):
    import_new_help_text = "Copy new adds from your shared folder to your local library"
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([import_command, arg])
    assert import_new_help_text in output
