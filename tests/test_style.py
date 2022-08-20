from pathlib import Path

from musicbros.style import DEFAULT_THEME, format_int_with_commas, get_theme


def test_read_theme(monkeypatch):
    def mock_home():
        return Path("/test_home")

    monkeypatch.setattr(Path, "home", mock_home)
    theme = get_theme()
    assert theme == DEFAULT_THEME


def test_format_int_with_commas():
    one_thousand = 1000
    expected_formatting = "1,000"
    one_thousand_with_comma = format_int_with_commas(one_thousand)
    assert one_thousand_with_comma == expected_formatting
