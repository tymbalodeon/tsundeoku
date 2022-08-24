from typer.testing import CliRunner

from musicbros import main
from musicbros.main import app
from tests.mocks import set_mock_home


def test_update_metadata_help(monkeypatch, tmp_path):
    def mock_get_argv() -> list[str]:
        return ["update-metadata", "-h"]

    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    set_mock_home(monkeypatch, tmp_path)
    update_metadata_help_text = "Update metadata according to the following rules:"
    remove_bracket_year_help_text = (
        'Remove bracketed years (e.g., "[2022]") from album fields'
    )
    expand_abbreviation_help_text = (
        'Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"'
    )
    remove_bracket_solo_help_text = (
        "[Optional] Remove bracketed solo instrument indications"
    )
    result = CliRunner().invoke(app, ["update-metadata", "-h"])
    stdout = result.stdout
    for help_text in [
        update_metadata_help_text,
        remove_bracket_year_help_text,
        expand_abbreviation_help_text,
        remove_bracket_solo_help_text,
    ]:
        assert help_text in stdout
    assert result.exit_code == 0
