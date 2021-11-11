from typer import Option, Typer, confirm, echo

from .config import print_config_values, write_config_options
from .import_new import get_album_directories, import_albums
from .strip_bracket_years import strip_bracket_years

app = Typer(help="CLI for managing the Musicbros audio file archive")


@app.command()
def config(update: bool = Option(False, "--update")):
    """
    Create (if config doesn't exist) or optionally update, and display config
    values
    """
    if update:
        write_config_options()
    print_config_values()


@app.command()
def import_new(strip_years: bool = Option(False, "--strip-years")):
    """
    Copy newly added audio files from your shared folder to your music library
    """
    echo("Importing newly added albums...")
    imports, errors, importable_error_albums = import_albums(get_album_directories())
    if imports and strip_years:
        strip_bracket_years()
    if (
        errors
        and importable_error_albums
        and confirm("Would you like to import all albums anyway?")
    ):
        imports, errors, importable_error_albums = import_albums(
            importable_error_albums, import_all=True
        )
        if imports and strip_years:
            strip_bracket_years()


@app.command()
def strip_years():
    """Remove bracketed years from album tags"""
    strip_bracket_years()
