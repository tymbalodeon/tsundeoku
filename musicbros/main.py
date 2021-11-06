from typer import Option, Typer, confirm, echo

from .config import print_config_values, write_config_options
from .import_new import import_complete_albums, import_error_albums
from .strip_bracket_years import strip_bracket_years

app = Typer(help="CLI for managing the Musicbros audio file archive")


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
    echo("Importing newly added albums...")
    imports, errors, bulk_fix_albums = import_complete_albums()
    if imports and strip_years:
        strip_bracket_years()
    elif errors:
        print("No new albums to import.")
        if confirm("Would you like to import all albums anyway?"):
            import_error_albums(bulk_fix_albums)
            if strip_years:
                strip_bracket_years()


@app.command()
def strip_years():
    """Remove bracketed years from album field"""
    strip_bracket_years()
