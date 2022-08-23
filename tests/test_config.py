from pathlib import Path

from musicbros.config import (
    get_config_directory,
    get_config_file,
    get_config_options,
    get_option_and_value,
)
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
    expected_shared_directory = tmp_path / "Dropbox"
    expected_pickle_file = tmp_path / ".config/beets/state.pickle"
    expected_ignored_directories = []
    expected_music_player = "Swinsian"
    assert text == (
        "[musicbros]\n"
        f"shared_directory = {expected_shared_directory}\n"
        f"pickle_file = {expected_pickle_file}\n"
        f"ignored_directories = {expected_ignored_directories}\n"
        f"music_player = {expected_music_player}\n"
    )


def get_expected_options_and_vaues():
    home = Path.home()
    expected_shared_directory = str(home / "Dropbox")
    expected_pickle_file = str(home / ".config/beets/state.pickle")
    expected_ignored_directories = "[]"
    expected_music_player = "Swinsian"
    return [
        ("shared_directory", expected_shared_directory),
        ("pickle_file", expected_pickle_file),
        ("ignored_directories", expected_ignored_directories),
        ("music_player", expected_music_player),
    ]


def check_option_and_value(expected_option, expected_value):
    option, value = get_option_and_value(expected_option)
    assert option == expected_option
    assert value == expected_value


def test_option_and_value_defaults(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    expected_options_and_values = get_expected_options_and_vaues()
    for expected_option, expected_value in expected_options_and_values:
        check_option_and_value(expected_option, expected_value)


def test_get_config_options(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    actual_options_and_values = get_config_options()
    expected_options_and_values = get_expected_options_and_vaues()
    actual_and_expected = zip(actual_options_and_values, expected_options_and_values)
    assert all(actual == expected for actual, expected in actual_and_expected)


def test_get_ignored_directories():
    pass
