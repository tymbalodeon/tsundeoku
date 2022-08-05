from rich.console import Console


def print_with_color(text: str | int, style="yellow"):
    if isinstance(text, int):
        text = f"{text:,}"
    Console().print(text, style=style)
