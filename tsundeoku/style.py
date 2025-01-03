def wrap_in_style(text: str, style: str) -> str:
    opening_tag = f"[{style}]"
    if "link" in style:
        link_tag = style.split("=")[0]
        closing_tag = f"[/{link_tag}]"
    else:
        closing_tag = f"[/{style}]"
    return f"{opening_tag}{text}{closing_tag}"


def stylize(text: str, styles: list[str] | str) -> str:
    if isinstance(styles, str):
        return wrap_in_style(text, styles)
    else:
        for style in styles:
            text = wrap_in_style(text, style)
    return text
