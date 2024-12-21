from typing import Annotated, cast

from cyclopts import App, Parameter
from cyclopts.config import Toml
from pync import notify

from tsundeoku.config.config import (
    APP_NAME,
    ReformatConfig,
    get_config_path,
    get_loaded_config,
)
from tsundeoku.config.main import config_app
from tsundeoku.import_new import import_new_albums
from tsundeoku.reformat import reformat_albums
from tsundeoku.schedule import schedule_app, send_email
from tsundeoku.style import StyleLevel, print_with_theme

app = App(
    default_parameter=Parameter(negative=()),
    config=Toml(get_config_path()),
    help="""
積んでおく // tsundeoku –– "to pile up for later"

Import audio files from a shared folder to a local library""",
)
app.command(config_app)
app.command(schedule_app)


@app.command(name="import")
def import_new(
    albums: Annotated[list[str] | None, Parameter(show=False)] = None,
    *,
    reformat=False,
    ask_before_disc_update=False,
    ask_before_artist_update=False,
    allow_prompt=False,
    is_scheduled_run: Annotated[bool, Parameter(show=False)] = False,
):
    """Copy new adds from your shared folder to your local library.

    Parameters
    ----------
    albums: list[str] | None
    reformat: bool
        Toggle reformatting
    ask_before_disc_update: bool
        Toggle confirming disc updates
    ask_before_artist_update: bool
        Toggle confirming removal of brackets from artist field
    allow_prompt: bool
        Toggle skipping imports that require user input
    is_scheduled_run: bool
    """
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


@app.command()
def reformat(
    *,
    remove_bracketed_years: bool | None = None,
    remove_bracketed_instruments: bool | None = None,
    expand_abbreviations: bool | None = None,
):
    """
    Reformat metadata according to the following rules:

    * Remove bracketeded years (e.g., "[2022]") from album fields. If the year
      field is blank, it will be updated with the year in bracketeds. If the year
      field contains a year different from the one in bracketeds, you will be
      asked whether you want to update the year field to match the bracketeded
      year.

    * Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"
      "Recordings," and "Original," respectively.

    * [Optional] Remove bracketeded solo instrument indications (e.g., "[solo
      piano]") from artist fields.

    Parameters
    ----------
    remove_bracketed_years: bool | None
        Remove bracketed years from album field
    remove_bracketed_instruments: bool | None
        Remove bracketed instrument indications from artist field
    expand_abbreviations: bool | None
        Expand abbreviations
    """
    reformat_settings = cast(ReformatConfig, get_loaded_config().reformat)
    if remove_bracketed_years is None:
        remove_bracketed_years_value = reformat_settings.remove_bracketed_years
    else:
        remove_bracketed_years_value = True
    if remove_bracketed_instruments is None:
        remove_bracketed_instruments_value = (
            reformat_settings.remove_bracketed_instruments
        )
    else:
        remove_bracketed_instruments_value = True
    if expand_abbreviations is None:
        expand_abbreviations_value = reformat_settings.expand_abbreviations
    else:
        expand_abbreviations_value = True
    reformat_albums(
        remove_bracketed_years_value,
        remove_bracketed_instruments_value,
        expand_abbreviations_value,
    )


def main():
    app()


if __name__ == "__main__":
    main()
