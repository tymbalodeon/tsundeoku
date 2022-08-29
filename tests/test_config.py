from pathlib import Path

from typer.testing import CliRunner

from tests.mocks import set_mock_home
from tsundeoku import config
from tsundeoku.config import get_config_directory, validate_music_player
from tsundeoku.main import app


def test_get_config_directory(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    config_directory = Path.home() / ".config/tsundeoku"
    assert not config_directory.exists()
    config_directory = get_config_directory()
    assert config_directory.exists()


def get_mock_shared_directories() -> str:
    shared_directories = str(Path.home() / "Dropbox")
    return f'["{shared_directories}"]'


def get_mock_pickle_file() -> Path:
    return Path.home() / ".config/beets/state.pickle"


def mock_get_config_value(_):
    return None


def test_config_help():
    config_help_text = (
        "Show config [default], show config path, edit config file in $EDITOR"
    )
    result = CliRunner().invoke(app, ["config", "-h"])
    assert config_help_text in result.output
    assert result.exit_code == 0


def mock_application_exists(command: str) -> bool:
    if "Swinsian" in command:
        return True
    return False


def mock_get_music_player():
    return None


def test_validate_music_player(monkeypatch):
    monkeypatch.setattr(config, "get_music_player", mock_get_music_player)
    error_message = validate_music_player()
    assert error_message and "WARNING" in error_message


def test_good_config(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "application_exists", mock_application_exists)
    shared_directories = tmp_path / "Dropbox"
    Path.mkdir(shared_directories)
    pickle_file = get_mock_pickle_file()
    Path.mkdir(pickle_file.parent, parents=True)
    pickle_file.touch()
    result = CliRunner().invoke(app, "config")
    output = result.output
    assert "WARNING" not in output
    assert result.exit_code == 0
