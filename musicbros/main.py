from typing import Optional

from typer import Argument, Context, Exit, Option, Typer, confirm, echo

from musicbros import __version__

from .config import update_or_print_config
from .import_new import get_album_directories, import_albums
from .remove_nonsense import remove_nonsense_if_as_is, remove_nonsense_main

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
    """Copy new adds from your shared folder to your library"""
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
    remove_nonsense_if_as_is(imports, as_is)
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
def remove_nonsense(
    solo_instruments: bool = Option(
        False,
        " /--remove-instruments",
        help='Remove bracketed "[solo <instrument>]" indications (time consuming).',
    )
):
    """Remove nonsense from tags"""
    remove_nonsense_main(solo_instruments)


def display_version(version: bool):
    if version:
        echo(f"musicbros {__version__}")
        raise Exit()


@app.callback(invoke_without_command=True)
def version(
    context: Context,
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
    elif not context.invoked_subcommand:
        import_new(as_is=False, skip_confirm_disc_overwrite=True)
