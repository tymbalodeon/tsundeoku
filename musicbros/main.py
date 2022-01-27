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
    as_is: bool = Option(
        False, "--as-is", help="Import new albums without altering metadata"
    ),
    skip_confirm_disc_overwrite: bool = Option(
        True,
        " /--confirm-disc-overwrite",
        help='Ask before applying default disc and disc total values of "1 out of 1"',
    ),
):
    """
    Copy newly added audio files from your shared folder to your music library
    """
    echo("Importing newly added albums...")
    imports, errors, importable_error_albums = import_albums(
        get_album_directories(), as_is, skip_confirm_disc_overwrite
    )
    if imports and not as_is:
        remove_nonsense_main()
    if (
        errors
        and importable_error_albums
        and confirm("Would you like to import all albums anyway?")
    ):
        imports, errors, importable_error_albums = import_albums(
            importable_error_albums, as_is, skip_confirm_disc_overwrite, import_all=True
        )
        if imports and not as_is:
            remove_nonsense_main()


@app.command()
def remove_nonsense(
    solo_instruments: bool = Option(
        False, help="Remove bracketed solo instrument indications (time consuming)."
    )
):
    """Remove nonsense from tags"""
    remove_nonsense_main(solo_instruments)
