from os import system

from typer import Option, Typer, confirm, echo

from .helpers import (
    get_album_dirs,
    import_complete_albums,
    set_quote,
    get_config_options,
)
from .strip_bracket_years import strip_bracket_years as strip_bracket_years_function

app = Typer(help="CLI for managing the Musicbros audio file archive")


def import_error_albums(albums):
    for album in albums:
        quote = set_quote(album)
        system(f"beet import {quote}{album}{quote}")
    strip_bracket_years_function()


@app.command()
def strip_years():
    strip_bracket_years_function()


@app.command()
def config():
    for value in get_config_options():
        echo(value)


@app.command()
def import_new(strip_years: bool = Option(False, "--strip-years")):
    """
    Copy newly added audio files from Dropbox to your music library location via
    beets
    """
    echo("Importing new albums...")
    new_imports, errors, bulk_fix_albums = import_complete_albums(get_album_dirs())
    if new_imports and strip_years:
        strip_bracket_years_function()
    elif errors:
        print("No new albums to import.")
        import_all = confirm(
            "Would you like to import all albums anyway?",
        )
        if import_all:
            import_error_albums(bulk_fix_albums)
