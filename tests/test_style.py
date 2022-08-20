from pathlib import Path

from musicbros import style
from musicbros.style import (
    DEFAULT_THEME,
    format_int_with_commas,
    get_theme,
    get_theme_config,
)


def test_get_theme(monkeypatch, tmp_path):
    custom_theme_path = tmp_path / "theme.ini"

    def mock_get_theme_config():
        return custom_theme_path

    monkeypatch.setattr(style, "get_theme_config", mock_get_theme_config)
    theme = get_theme()
    assert theme == DEFAULT_THEME
    custom_theme = "[styles]\ninfo = dim cyan\nwarning = magenta\nerror = bold red"
    custom_theme_path.write_text(custom_theme)
    theme = get_theme()
    assert theme != DEFAULT_THEME


def test_get_theme_config(monkeypatch):
    def mock_home():
        return Path("/test_home")

    monkeypatch.setattr(Path, "home", mock_home)
    expected_theme_config = "/test_home/.config/musicbros/theme.ini"
    theme_config = get_theme_config()
    assert theme_config == expected_theme_config


def test_format_int_with_commas():
    one_thousand = 1000
    expected_formatting = "1,000"
    one_thousand_with_comma = format_int_with_commas(one_thousand)
    assert one_thousand_with_comma == expected_formatting
