from typer.testing import CliRunner

from tests.mocks import set_mock_home
from tsundeoku import main
from tsundeoku.main import tsundeoku


def test_reformat_help(monkeypatch, tmp_path):
    reformat_help_args = ["reformat", "-h"]

    def mock_get_argv() -> list[str]:
        return reformat_help_args

    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    set_mock_home(monkeypatch, tmp_path)
    reformat_help_text = "Reformat metadata according to the following rules:"
    remove_bracket_year_help_text = (
        'Remove bracketed years (e.g., "[2022]") from album fields'
    )
    expand_abbreviation_help_text = (
        'Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"'
    )
    remove_bracket_solo_help_text = (
        "[Optional] Remove bracketed solo instrument indications"
    )
    result = CliRunner().invoke(tsundeoku, reformat_help_args)
    output = result.output
    for help_text in [
        reformat_help_text,
        remove_bracket_year_help_text,
        expand_abbreviation_help_text,
        remove_bracket_solo_help_text,
    ]:
        assert help_text in output
    assert result.exit_code == 0
