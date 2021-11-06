from os import system

from typer import Typer, confirm, echo

from .helpers import NEW_ALBUMS, import_complete_albums, set_quote
from .strip_bracket_years import strip_bracket_years

app = Typer(help="CLI for managing the Musicbros audio file archive")


def import_error_albums(albums):
    for album in albums:
        quote = set_quote(album)
        system(f"beet import {quote}{album}{quote}")
    strip_years()


@app.command()
def strip_years():
    strip_bracket_years()


@app.command()
def new():
    """
    Copy newly added audio files from Dropbox to your music library location via
    beets
    """
    echo("Importing new albums...")
    new_imports, errors, bulk_fix_albums = import_complete_albums(NEW_ALBUMS)
    if new_imports:
        strip_years()
    elif errors:
        print("No new albums to import.")
        import_all = confirm(
            "Would you like to import all albums anyway?",
        )
        if import_all:
            import_error_albums(bulk_fix_albums)
