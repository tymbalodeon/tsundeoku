from pytest import mark
from typer.testing import CliRunner

from tsundeoku import main
from tsundeoku.main import tsundeoku

from .conftest import get_mock_get_argvs, mock_argv

reformat_command = "reformat"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs(reformat_command)

help_texts = [
    "Reformat metadata according to the following rules:",
    'Remove bracketed years (e.g., "[2022]") from album fields',
    'Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"',
    "[Optional] Remove bracketed solo instrument indications",
]


def get_args() -> list[tuple[str, mock_argv, str]]:
    args = []
    for help_text in help_texts:
        args.append(("--help", mock_get_argv_long, help_text))
        args.append(("-h", mock_get_argv_short, help_text))
    return args


@mark.parametrize("arg, mock_get_argv, help_text", get_args())
def test_reformat_help(arg, mock_get_argv, help_text, monkeypatch):
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = CliRunner().invoke(tsundeoku, [reformat_command, arg]).output
    assert help_text in output
