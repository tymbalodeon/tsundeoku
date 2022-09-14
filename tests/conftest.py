from pytest import fixture
from pathlib import Path


@fixture(autouse=True)
def set_mock_home(monkeypatch, tmp_path_factory):
    def mock_home():
        home = tmp_path_factory.mktemp("home")
        return home

    monkeypatch.setattr(Path, "home", mock_home)
