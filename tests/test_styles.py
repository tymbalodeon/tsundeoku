from pytest import mark
from tsundeoku.style import stylize

expected_styles = [
    ("text", "blue", "[blue]text[/blue]"),
    ("text", ["bold", "yellow"], "[yellow][bold]text[/bold][/yellow]"),
]


@mark.parametrize("text, styles, expected", expected_styles)
def test_stylize(text, styles, expected):
    styled = stylize(text, styles)
    assert styled == expected
