from pathlib import Path

from pytest import CaptureFixture, mark

from tsundeoku.config.main import stylize_path
from tsundeoku.style import StyleLevel, print_with_theme, stylize

expected_styles = [
    ("text", "blue", "[blue]text[/blue]"),
    ("text", ["bold", "yellow"], "[yellow][bold]text[/bold][/yellow]"),
]


@mark.parametrize("text, styles, expected", expected_styles)
def test_stylize(text: str, styles: list[str] | str, expected: str):
    styled = stylize(text, styles)
    assert styled == expected


def test_print_with_theme_default(capfd: CaptureFixture):
    print_with_theme("text")
    output = capfd.readouterr().out
    assert output == "text\n"


def test_print_with_theme(capfd: CaptureFixture):
    print_with_theme("text", level=StyleLevel.ERROR)
    output = capfd.readouterr().out
    assert output == "text\n"


def test_stylize_path():
    path = Path("/tmp")
    expected_stylized_path = '[green]"/tmp"[/green]'
    stylized_path = stylize_path(str(path))
    assert stylized_path == expected_stylized_path
