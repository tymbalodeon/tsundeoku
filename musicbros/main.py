from typing import Optional

from typer import Argument, Exit, Option, Typer, confirm, echo

from musicbros import __version__

from .config import print_config_values, update_or_print_config, validate_config
from .import_new import get_album_directories, import_albums
from .update_metadata import update_metadata_if_as_is, update_metadata_main

app = Typer(
    help=(
        f"musicbros ({__version__}) -- A CLI for managing imports from a shared folder"
        ' to a "beets" library'
    ),
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


@app.command()
def config(update: bool = Option(False, "--update", "-u")):
    """Create, update, and display config values"""
    update_or_print_config(update)


@app.command()
def import_new(
    as_is: bool = Option(
        False, "--as-is", help="Import new albums without altering metadata"
    ),
    skip_confirm_disc_overwrite: bool = Option(
        True,
        " /--confirm-overwrite-discs",
        help='Confirm applying default disc and disc total values of "1 out of 1"',
    ),
    albums: Optional[list[str]] = Argument(None, hidden=False),
):
    """Copy new adds from your shared folder to your "beets" library"""
    echo("Importing newly added albums...")
    first_time = False
    if not isinstance(albums, list):
        first_time = True
        albums = get_album_directories()
    imports, errors, importable_error_albums = import_albums(
        albums,
        as_is,
        skip_confirm_disc_overwrite,
        import_all=not first_time,
    )
    update_metadata_if_as_is(imports, as_is)
    if (
        first_time
        and errors
        and importable_error_albums
        and confirm("Would you like to import all albums anyway?")
    ):
        import_new(
            as_is=as_is,
            skip_confirm_disc_overwrite=skip_confirm_disc_overwrite,
            albums=importable_error_albums,
        )


@app.command()
def update_metadata(
    solo_instruments: bool = Option(
        False,
        " /--remove-instruments",
        help='Remove bracketed "[solo <instrument>]" indications (time consuming).',
    )
):
    """
    Update metadata according to the following rules:

    * Remove bracketed years (e.g., "[2022]") from album fields. If the year
      field is blank, it will be updated with the year in brackets. If the year
      field contains a year different from the one in brackets, you will be
      asked whether you want to update the year field to match the bracketed
      year.

    * Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"
      "Recordings," and "Original," respectively.

    * [Optional] Remove bracketed solo instrument indications (e.g., "[solo
      piano]") from artist fields.
    """
    update_metadata_main(solo_instruments)


def display_version(version: bool):
    if version:
        echo(f"musicbros {__version__}")
        raise Exit()


@app.callback(invoke_without_command=True)
def version(
    version: bool = Option(
        False,
        "--version",
        "-V",
        callback=display_version,
        help="Display version number",
    ),
):
    if version:
        return
    import_new(as_is=False, skip_confirm_disc_overwrite=True)
