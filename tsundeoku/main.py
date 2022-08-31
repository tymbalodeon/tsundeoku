from sys import argv

from pydantic import ValidationError
from rich import print
from rich.markup import escape
from rich.prompt import Confirm
from typer import Argument, Context, Exit, Option, Typer

from tsundeoku import __version__

from .config.config import (
    STATE,
    StyleLevel,
    get_config,
    get_loaded_config,
    print_errors,
    print_with_theme,
)
from .config.main import config_command
from .import_new import get_albums, import_albums
from .reformat import reformat_albums

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
        print_errors(error, level=StyleLevel.WARNING)
    subcommand = context.invoked_subcommand
    if is_valid:
        if not subcommand:
            import_new(
                reformat=False,
                ask_before_disc_update=False,
                ask_before_artist_update=False,
                allow_prompt=True,
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
    reformat: bool = Option(
        None,
        "--reformat/--as-is",
        help="Import new albums without altering metadata.",
        show_default=False,
    ),
    ask_before_disc_update: bool = Option(
        None,
        "--ask-before-disc-update/--auto-update-disc",
        help=(
            'Prompt for confirmation to apply default disc and disc total values of "1'
            ' out of 1".'
        ),
        show_default=False,
    ),
    ask_before_artist_update: bool = Option(
        None,
        "--ask-before-artist-update/--auto-update-artist",
        help=(
            f'Prompt for confirmation to remove bracketed "{solo_instrument}"'
            " indications."
        ),
        show_default=False,
    ),
    allow_prompt: bool = Option(
        None,
        "--allow-prompt/--disallow-prompt",
        help="Allow prompts for user confirmation to update metadata.",
        show_default=False,
    ),
):
    """Copy new adds from your shared folder to your local library"""
    print("Importing newly added albums...")
    config = get_loaded_config()
    import_settings = config.import_new
    if reformat is None:
        reformat = import_settings.reformat
    if ask_before_disc_update is None:
        ask_before_disc_update = import_settings.ask_before_disc_update
    if ask_before_artist_update is None:
        ask_before_artist_update = import_settings.ask_before_artist_update
    if allow_prompt is None:
        allow_prompt = import_settings.allow_prompt
    first_time = False
    if not albums:
        first_time = True
        albums = get_albums()
    imports, errors, importable_error_albums = import_albums(
        albums,
        reformat,
        ask_before_disc_update,
        ask_before_artist_update,
        import_all=not first_time,
        prompt=allow_prompt,
    )
    if imports and reformat:
        reformat_settings = config.reformat
        remove_bracket_years = reformat_settings.remove_bracket_years
        remove_bracket_instruments = reformat_settings.remove_bracket_instruments
        expand_abbreviations = reformat_settings.expand_abbreviations
        reformat_albums(
            remove_bracket_years, remove_bracket_instruments, expand_abbreviations
        )
    if (
        first_time
        and errors
        and importable_error_albums
        and Confirm.ask("Would you like to import all albums anyway?")
    ):
        import_new(
            albums=importable_error_albums,
            reformat=reformat,
            ask_before_disc_update=ask_before_disc_update,
            ask_before_artist_update=ask_before_artist_update,
            allow_prompt=allow_prompt,
        )


@tsundeoku.command()
def reformat(
    remove_bracket_years: bool = Option(
        None,
        "--remove-bracket-years/--years-as-is",
        help="Remove bracket years from album field.",
        show_default=False,
    ),
    remove_bracket_instruments: bool = Option(
        None,
        "--remove-bracket-instruments/--instruments-as-is",
        help="Remove bracket instrument indications from artist field.",
        show_default=False,
    ),
    expand_abbreviations: bool = Option(
        None,
        "--expand-abbreviations/--abbreviations-as-is",
        help="Expand abbreviations.",
        show_default=False,
    ),
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
    reformat_settings = get_loaded_config().reformat
    if remove_bracket_years is None:
        remove_bracket_years = reformat_settings.remove_bracket_years
    if remove_bracket_instruments is None:
        remove_bracket_instruments = reformat_settings.remove_bracket_instruments
    if expand_abbreviations is None:
        expand_abbreviations = reformat_settings.expand_abbreviations
    reformat_albums(
        remove_bracket_years, remove_bracket_instruments, expand_abbreviations
    )
