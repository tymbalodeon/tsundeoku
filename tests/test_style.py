from pytest import mark

from tsundeoku.style import StyleLevel, print_with_theme, stylize

expected_styles = [
    ("text", "blue", "[blue]text[/blue]"),
    ("text", ["bold", "yellow"], "[yellow][bold]text[/bold][/yellow]"),
]


@mark.parametrize("text, styles, expected", expected_styles)
def test_stylize(text, styles, expected):
    styled = stylize(text, styles)
    assert styled == expected


def test_print_with_theme_default(capfd):
    print_with_theme("text")
    output = capfd.readouterr().out
    assert output == "text\n"


def test_print_with_theme(capfd):
    print_with_theme("text", level=StyleLevel.ERROR)
    output = capfd.readouterr().out
    assert output == "text\n"
