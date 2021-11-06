from os import system

from typer import Option, Typer, confirm, echo

from .config import write_config_options
from .helpers import (
    get_album_dirs,
    import_complete_albums,
    print_config_values,
    set_quote,
)
from .strip_bracket_years import strip_bracket_years as strip_bracket_years_function

app = Typer(help="CLI for managing the Musicbros audio file archive")


def import_error_albums(albums):
    for album in albums:
        quote = set_quote(album)
        system(f"beet import {quote}{album}{quote}")
    strip_bracket_years_function()


@app.command()
def config(update: bool = Option(False, "--update")):
    """Create (if config doesn't exist) or optionally update, and display config values"""
    if update:
        write_config_options()
    print_config_values()


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


@app.command()
def strip_years():
    """Remove bracketed years from album field"""
    strip_bracket_years_function()
