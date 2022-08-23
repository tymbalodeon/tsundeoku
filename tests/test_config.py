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
    assert text == (
        "[musicbros]\n"
        "shared_directory =\n"
        "pickle_file =\n"
        "ignored_directories =\n"
        "music_player =\n"
    )


def check_option_and_value(option):
    config_option, value = get_option_and_value(option)
    assert config_option == option
    assert value == ""


def test_option_and_value_defaults(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    for option in [
        "shared_directory",
        "pickle_file",
        "ignored_directories",
        "music_player",
    ]:
        check_option_and_value(option)


def test_get_config_options(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    config_options = get_config_options()
    expected_config_options = [
        ("shared_directory", ""),
        ("pickle_file", ""),
        ("ignored_directories", ""),
        ("music_player", ""),
    ]
    actual_and_expected = zip(config_options, expected_config_options)
    assert all(actual == expected for actual, expected in actual_and_expected)
