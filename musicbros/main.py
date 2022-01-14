from typer import Option, Typer, confirm, echo

from .config import print_config_values, write_config_options
from .import_new import get_album_directories, import_albums
from .remove_nonsense import remove_nonsense_main

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
def import_new(
    remove_nonsense: bool = Option(True, "--remove-nonsense"),
    confirm_update_year: bool = Option(False, "--confirm-update-year"),
):
    """
    Copy newly added audio files from your shared folder to your music library
    """
    echo("Importing newly added albums...")
    imports, errors, importable_error_albums = import_albums(
        get_album_directories(), confirm_update_year
    )
    if imports and remove_nonsense:
        remove_nonsense_main()
    if (
        errors
        and importable_error_albums
        and confirm("Would you like to import all albums anyway?")
    ):
        imports, errors, importable_error_albums = import_albums(
            importable_error_albums, confirm_update_year, import_all=True
        )
        if imports and remove_nonsense:
            remove_nonsense_main()


@app.command()
def remove_nonsense():
    """Remove nonsense from tags"""
    remove_nonsense_main()
