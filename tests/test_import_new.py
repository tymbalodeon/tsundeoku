from pathlib import Path

from typer.testing import CliRunner

from tsundeoku import config, main
from tsundeoku.config import get_shared_directories
from tsundeoku.import_new import get_albums
from tsundeoku.main import app

from .mocks import set_mock_home


def test_get_albums(monkeypatch, tmp_path):
    def mock_get_config_value(_):
        pass

    set_mock_home(monkeypatch, tmp_path)
    albums = get_albums()
    assert albums == []
    shared_directory = get_shared_directories()[0]
    mock_album = Path(shared_directory) / "Album"
    Path.mkdir(mock_album, parents=True)
    mock_track = mock_album / "Track"
    mock_track.touch()
    albums = get_albums()
    assert len(albums)
    monkeypatch.setattr(config, "get_config_value", mock_get_config_value)
    albums = get_albums()
    assert albums == []


def test_import_new_help(monkeypatch, tmp_path):
    def mock_get_argv() -> list[str]:
        return ["import", "-h"]

    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    set_mock_home(monkeypatch, tmp_path)
    import_new_help_text = (
        'Copy new adds from your shared folder to your "beets" library'
    )
    result = CliRunner().invoke(app, ["import", "-h"])
    assert import_new_help_text in result.output
    assert result.exit_code == 0
