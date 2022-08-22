from pathlib import Path


def set_mock_home(monkeypatch, tmp_path):
    def mock_home():
        return tmp_path

    monkeypatch.setattr(Path, "home", mock_home)
