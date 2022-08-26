from typer.testing import CliRunner

from tsundeoku import main
from tsundeoku.main import app

from .mocks import set_mock_home


def test_import_new_help(monkeypatch, tmp_path):
    def mock_get_argv() -> list[str]:
        return ["import-new", "-h"]

    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    set_mock_home(monkeypatch, tmp_path)
    import_new_help_text = (
        'Copy new adds from your shared folder to your "beets" library'
    )
    result = CliRunner().invoke(app, ["import-new", "-h"])
    assert import_new_help_text in result.stdout
    assert result.exit_code == 0
