from pytest import MonkeyPatch, mark

from tsundeoku import main

from .conftest import MockArgV, call_command, get_help_args

import_command = "import"


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_import_help(
    arg: str, mock_get_argv: MockArgV, monkeypatch: MonkeyPatch
):
    import_new_help_text = (
        "Copy new adds from your shared folder to your local library"
    )
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = call_command([import_command, arg])
    assert import_new_help_text in output
