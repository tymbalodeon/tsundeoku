from sys import argv

from pydantic import ValidationError
from rich import print
from rich.markup import escape
from rich.prompt import Confirm
from typer import Argument, Context, Exit, Option, Typer

from tsundeoku import __version__

from .config.config import STATE, StyleLevel, get_config, print_errors, print_with_theme
from .config.main import config_command
from .import_new import get_albums, import_albums
from .reformat import reformat_main

tsundeoku = Typer(
    help="CLI for importing audio files from a shared folder to a local library",
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    rich_markup_mode="rich",
)
tsundeoku.add_typer(config_command, name="config")


def display_version(version: bool):
    if version:
        print(f"tsundeoku {__version__}")
        raise Exit()


def get_argv() -> list[str]:
    return argv


def skip_validation(context: Context) -> bool:
    skip_options = context.help_option_names + [
        "--path",
        "-p",
        "--file",
        "-f",
        "--edit",
        "-e",
        "--reset",
    ]
    for option in skip_options:
        if option in get_argv():
            return True
    return False


@tsundeoku.callback()
def callback(
    context: Context,
    _: bool = Option(
        False,
        "--version",
        "-v",
        callback=display_version,
        help="Display version number",
    ),
):
    if skip_validation(context):
        return
    is_valid = True
    try:
        STATE["config"] = get_config()
    except ValidationError as error:
        is_valid = False
        if context.invoked_subcommand != "config":
            print_errors(error, level=StyleLevel.WARNING)
    subcommand = context.invoked_subcommand
    if is_valid:
        if not subcommand:
            import_new(
                as_is=False,
                ask_before_disc_update=False,
                ask_before_artist_update=False,
                prompt=True,
                albums=[],
            )
        return
    if not subcommand or subcommand in {"import", "update-metadata"}:
        print_with_theme("ERROR: invalid config", level=StyleLevel.ERROR)
        raise Exit(1)


solo_instrument = escape("[solo <instrument>]")


@tsundeoku.command(name="import")
def import_new(
    albums: list[str] = Argument(None, hidden=True),
    as_is: bool = Option(
        False, "--as-is", help="Import new albums without altering metadata."
    ),
    ask_before_disc_update: bool = Option(
        False,
        "--ask-before-disc-update",
        help=(
            'Prompt for confirmation to apply default disc and disc total values of "1'
            ' out of 1".'
        ),
    ),
    ask_before_artist_update: bool = Option(
        False,
        "--ask-before-artist-update",
        help=(
            f'Prompt for confirmation to remove bracketed "{solo_instrument}"'
            " indications."
        ),
    ),
    prompt: bool = Option(
        True,
        " /--disallow-prompt",
        help="Allow prompts for user confirmation to update metadata.",
    ),
):
    """Copy new adds from your shared folder to your local library"""
    print("Importing newly added albums...")
    first_time = False
    if not albums:
        first_time = True
        albums = get_albums()
    imports, errors, importable_error_albums = import_albums(
        albums,
        as_is,
        ask_before_disc_update,
        ask_before_artist_update,
        import_all=not first_time,
        prompt=prompt,
    )
    if imports and not as_is:
        reformat_main()
    if (
        first_time
        and errors
        and importable_error_albums
        and Confirm.ask("Would you like to import all albums anyway?")
    ):
        import_new(
            albums=importable_error_albums,
            as_is=as_is,
            ask_before_disc_update=ask_before_disc_update,
            ask_before_artist_update=ask_before_artist_update,
            prompt=prompt,
        )


@tsundeoku.command()
def reformat(
    solo_instruments: bool = Option(
        False,
        "--remove-instruments/ ",
        help=f'Remove bracketed "{solo_instrument}" indications (time consuming).',
    )
):
    """
    Reformat metadata according to the following rules:

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
    reformat_main(solo_instruments)
