from pytest import mark
from typer.testing import CliRunner

from tsundeoku import main
from tsundeoku.main import tsundeoku

from .conftest import get_mock_get_argvs

import_command = "import"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs(import_command)


@mark.parametrize(
    "arg, mock_get_argv", [("--help", mock_get_argv_long), ("-h", mock_get_argv_short)]
)
def test_import_help(arg, mock_get_argv, monkeypatch):
    import_new_help_text = "Copy new adds from your shared folder to your local library"
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = CliRunner().invoke(tsundeoku, [import_command, arg]).output
    assert import_new_help_text in output
