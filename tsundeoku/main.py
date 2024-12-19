from cyclopts import App

from tsundeoku.config.config import APP_NAME, get_loaded_config
from tsundeoku.style import StyleLevel, print_with_theme, stylize

from pync import notify
from .config.main import config

from .import_new import import_new_albums
from .schedule import send_email

# from .reformat import reformat_albums
from .schedule import schedule


def get_name_definition() -> str:
    app_name = '積んでおく("tsundeoku")'
    app_name = stylize(app_name, styles="bright_green")
    definition = stylize("to pile up for later", styles="italic")
    app_name = f'{app_name}: "{definition}"'
    return stylize(app_name, styles="bold")


tsundeoku = App(
    help=(
        f"{get_name_definition()}\n\n"
        "Import audio files from a shared folder to a local library."
    ),
)
tsundeoku.command(config, name="config")
tsundeoku.command(schedule, name="schedule")


# def display_version(version: bool):
#     if version:
#         return f"tsundeoku {__version__}"


# def get_argv() -> list[str]:
#     return argv


# def skip_validation(context: Context) -> bool:
#     skip_options = context.help_option_names + [
#         "--path",
#         "-p",
#         "--file",
#         "-f",
#         "--edit",
#         "-e",
#         "--reset",
#     ]
#     for option in skip_options:
#         if option in get_argv():
#             return True
#     return False


# @tsundeoku.callback()
# def callback(
#     context: Context,
#     _: bool = Option(
#         False,
#         "--version",
#         "-V",
#         callback=display_version,
#         help="Display version number.",
#     ),
# ):
#     if skip_validation(context):
#         return
#     is_valid = True
#     try:
#         STATE["config"] = get_config()
#     except ValidationError as error:
#         is_valid = False
#         print_errors(error, level=StyleLevel.WARNING)
#     subcommand = context.invoked_subcommand
#     if is_valid:
#         if not subcommand:
#             import_new(
#                 reformat=False,
#                 ask_before_disc_update=False,
#                 ask_before_artist_update=False,
#                 allow_prompt=True,
#                 albums=[],
#             )
#         return
#     if not subcommand or subcommand in {"import", "update-metadata"}:
#         print_with_theme("ERROR: invalid config", level=StyleLevel.ERROR)
#         raise Exit(1)


# solo_instrument = escape("[solo <instrument>]")

# albums: list[str] = Argument(None, hidden=True),
# reformat: bool = Option(
#     None,
#     "--reformat/--as-is",
#     help="Import new albums without altering metadata.",
#     show_default=False,
# ),
# ask_before_disc_update: bool = Option(
#     None,
#     "--ask-before-disc-update/--auto-update-disc",
#     help=(
#         "Prompt for confirmation to apply default disc and disc total"
#         ' values of "1 out of 1".'
#     ),
#     show_default=False,
# ),
# ask_before_artist_update: bool = Option(
#     None,
#     "--ask-before-artist-update/--auto-update-artist",
#     help=(
#         f'Prompt for confirmation to remove bracketed "{solo_instrument}"'
#         " indications."
#     ),
#     show_default=False,
# ),
# allow_prompt: bool = Option(
#     None,
#     "--allow-prompt/--disallow-prompt",
#     help="Allow prompts for user confirmation to update metadata.",
#     show_default=False,
# ),
# is_scheduled_run: bool = Option(False, "--scheduled-run", hidden=True),


@tsundeoku.command(name="import")
def import_new(
    albums: list[str] | None = None,
    reformat=False,
    ask_before_disc_update=False,
    ask_before_artist_update=False,
    allow_prompt=False,
    is_scheduled_run=False,
):
    """Copy new adds from your shared folder to your local library."""
    try:
        if albums is None:
            albums = []
        import_new_albums(
            albums,
            reformat,
            ask_before_disc_update,
            ask_before_artist_update,
            allow_prompt,
            is_scheduled_run,
        )
    except Exception as error:
        if repr(error) == "exit":
            return
        if is_scheduled_run:
            config = get_loaded_config()
            email_on = config.notifications.email_on
            system_on = config.notifications.system_on
            if email_on or system_on:
                subject = "ERROR"
                contents = str(error)
                if email_on:
                    send_email(subject, contents)
                if system_on:
                    notify(contents, title=APP_NAME)
        print_with_theme(str(error), level=StyleLevel.ERROR)


# @tsundeoku.command()
# def reformat(
#     remove_bracket_years: bool = Option(
#         None,
#         "--remove-bracket-years/--years-as-is",
#         help="Remove bracket years from album field.",
#         show_default=False,
#     ),
#     remove_bracket_instruments: bool = Option(
#         None,
#         "--remove-bracket-instruments/--instruments-as-is",
#         help="Remove bracket instrument indications from artist field.",
#         show_default=False,
#     ),
#     expand_abbreviations: bool = Option(
#         None,
#         "--expand-abbreviations/--abbreviations-as-is",
#         help="Expand abbreviations.",
#         show_default=False,
#     ),
# ):
#     """
#     Reformat metadata according to the following rules:

#     * Remove bracketed years (e.g., "[2022]") from album fields. If the year
#       field is blank, it will be updated with the year in brackets. If the year
#       field contains a year different from the one in brackets, you will be
#       asked whether you want to update the year field to match the bracketed
#       year.

#     * Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"
#       "Recordings," and "Original," respectively.

#     * [Optional] Remove bracketed solo instrument indications (e.g., "[solo
#       piano]") from artist fields.
#     """
#     reformat_settings = get_loaded_config().reformat
#     if remove_bracket_years is None:
#         remove_bracket_years = reformat_settings.remove_bracket_years
#     if remove_bracket_instruments is None:
#         remove_bracket_instruments = reformat_settings.remove_bracket_instruments
#     if expand_abbreviations is None:
#         expand_abbreviations = reformat_settings.expand_abbreviations
#     reformat_albums(
#         remove_bracket_years, remove_bracket_instruments, expand_abbreviations
#     )
