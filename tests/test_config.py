from pathlib import Path

from musicbros.config import get_config_directory, get_config_file
from tests.mocks import set_mock_home


def test_get_config_directory(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    config_directory = Path.home() / ".config/musicbros"
    assert not config_directory.exists()
    config_directory = get_config_directory()
    assert config_directory.exists()


def test_get_config_file(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    config_directory = get_config_directory()
    config_file = config_directory / "musicbros.ini"
    assert not config_file.exists()
    config_file = get_config_file()
    assert config_file.exists()
    text = config_file.read_text()
    assert text == "[musicbros]\n"
