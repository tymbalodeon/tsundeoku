from os import environ
from subprocess import call
from sys import argv

from rich import print
from rich.prompt import Confirm
from typer import Argument, Context, Exit, Option, Typer

from musicbros import __version__
from musicbros.style import PrintLevel, print_with_color

from .config import get_config_path, print_config_values, validate_config
from .import_new import get_album_directories, import_albums
from .update_metadata import update_metadata_main

app = Typer(
    help='CLI for managing imports from a shared folder to a "beets" library',
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


def display_version(version: bool):
    if version:
        print(f"musicbros {__version__}")
        raise Exit()


def get_argv() -> list[str]:
    return argv


def skip_validation(context) -> bool:
    info_options = context.help_option_names + ["--path", "-p", "--edit", "-e"]
    for option in info_options:
        if option in get_argv():
            return True
    return False


@app.callback(invoke_without_command=True)
def callback(
    context: Context,
    _: bool = Option(
        False,
        "--version",
        "-V",
        callback=display_version,
        help="Display version number",
    ),
):
    if skip_validation(context):
        return
    is_valid = validate_config()
    subcommand = context.invoked_subcommand
    if is_valid:
        if not subcommand:
            import_new(
                as_is=False,
                ask_before_disc_update=False,
                ask_before_artist_update=False,
                prompt=True,
                albums=None,
            )
        return
    if not subcommand or subcommand in {"import-new", "update-metadata"}:
        print_with_color("ERROR: invalid config", PrintLevel.ERROR)
        raise Exit(1)


@app.command()
def config(
    path: bool = Option(False, "--path", "-p", help="Show config file path"),
    edit: bool = Option(False, "--edit", "-e", help="Edit config file with $EDITOR"),
):
    """Display config [default], display config path, edit config file in $EDITOR"""
    config_path = get_config_path()
    if path:
        print(config_path)
    elif edit:
        editor = environ.get("EDITOR", "vim")
        call([editor, config_path])
    else:
        print_config_values()


@app.command()
def import_new(
    as_is: bool = Option(
        False, "--as-is", help="Import new albums without altering metadata"
    ),
    ask_before_disc_update: bool = Option(
        False,
        "--ask-before-disc-update",
        help=(
            'Prompt for confirmation to apply default disc and disc total values of "1'
            ' out of 1"'
        ),
    ),
    ask_before_artist_update: bool = Option(
        False,
        "--ask-before-artist-update",
        help=(
            'Prompt for confirmation to remove bracketed "[solo <instrument>]"'
            " indications"
        ),
    ),
    prompt: bool = Option(
        True,
        " /--disallow-prompt",
        help="Allow prompts for user confirmation to update metadata",
    ),
    albums: list[str] = Argument(None, hidden=False),
):
    """Copy new adds from your shared folder to your "beets" library"""
    print("Importing newly added albums...")
    first_time = False
    if not albums:
        first_time = True
        albums = get_album_directories()
    imports, errors, importable_error_albums = import_albums(
        albums,
        as_is,
        ask_before_disc_update,
        ask_before_artist_update,
        import_all=not first_time,
        prompt=prompt,
    )
    if imports and not as_is:
        update_metadata_main()
    if (
        first_time
        and errors
        and importable_error_albums
        and Confirm.ask("Would you like to import all albums anyway?")
    ):
        import_new(
            as_is=as_is,
            ask_before_disc_update=ask_before_disc_update,
            ask_before_artist_update=ask_before_artist_update,
            albums=importable_error_albums,
            prompt=prompt,
        )


@app.command()
def update_metadata(
    solo_instruments: bool = Option(
        False,
        "--remove-instruments/ ",
        help='Remove bracketed "[solo <instrument>]" indications (time consuming).',
    )
):
    """
    Update metadata according to the following rules:

    \b
    * Remove bracketed years (e.g., "[2022]") from album fields. If the year
      field is blank, it will be updated with the year in brackets. If the year
      field contains a year different from the one in brackets, you will be
      asked whether you want to update the year field to match the bracketed
      year.

    \b
    * Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"
      "Recordings," and "Original," respectively.

    \b
    * [Optional] Remove bracketed solo instrument indications (e.g., "[solo
      piano]") from artist fields.
    """
    update_metadata_main(solo_instruments)
