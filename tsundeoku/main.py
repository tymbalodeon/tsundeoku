import fnmatch
import re
from glob import glob
from pathlib import Path
from typing import Annotated, cast

import mutagen
from cyclopts import App, Parameter
from cyclopts.config import Toml
from cyclopts.validators import Path as PathValidator
from pync import notify
from rich import print
from tinytag import TinyTag

from tsundeoku.config import (
    Config,
    config_app,
    get_app_name,
    get_config_path,
    is_toml,
    parse_path,
)
from tsundeoku.import_new import import_new_files
from tsundeoku.reformat import reformat_albums
from tsundeoku.schedule import schedule_app, send_email
from tsundeoku.style import StyleLevel, print_with_theme

app = App(
    # default_parameter=Parameter(negative=()),
    config=Toml(get_config_path()),
    help="""
積んでおく // tsundeoku –– "to pile up for later"

Import audio files from a shared folder to a local library""",
)
app.command(config_app)
app.command(schedule_app)


@app.command(name="import")
def import_new(
    *,
    reformat=False,
    ask_before_disc_update: Annotated[
        bool, Parameter(negative="--auto-update-disc")
    ] = False,
    ask_before_artist_update: Annotated[
        bool, Parameter(negative="--auto-update-artist")
    ] = False,
    allow_prompt: Annotated[
        bool, Parameter(negative="--disallow-prompt")
    ] = False,
    config_path: Annotated[
        Path,
        Parameter(
            converter=parse_path,
            validator=(PathValidator(exists=True, dir_okay=False), is_toml),
        ),
    ] = get_config_path(),
    is_scheduled_run: Annotated[bool, Parameter(show=False)] = False,
):
    """Copy new adds from your shared folder to your local library.

    Parameters
    ----------
    reformat: bool
        Toggle reformatting.
    ask_before_disc_update: bool
        Toggle confirming disc updates.
    ask_before_artist_update: bool
        Toggle confirming removal of brackets from artist field.
    allow_prompt: bool
        Toggle skipping imports that require user input.
    """
    config = Config.from_toml(config_path)
    for directory in config.items.files.shared_directories:
        for extension in (
            "*.aac",
            "*.aiff",
            "*.flac",
            "*.m4a",
            "*.mp3",
            "*.wav",
        ):
            for file in glob(f"{directory}/**/{extension}", recursive=True):
                if reformat:
                    tags = TinyTag.get(file)
                    print(tags.artist, tags.album, tags.disc)
                print(file)
            # metadata = mutagen.File(file, easy=True)
            # if metadata is not None:
            #     print(vars(metadata.tags))
            #     for key, value in metadata.tags.items():
            #         if isinstance(value, list):
            #             for v in value:
            #                 if isinstance(v, str):
            #                     print({key: value})
            #         else:
            #             print({key: value})
    # try:
    #     import_new_files(
    #         reformat=reformat,
    #         ask_before_disc_update=ask_before_disc_update,
    #         ask_before_artist_update=ask_before_artist_update,
    #         allow_prompt=allow_prompt,
    #         is_scheduled_run=is_scheduled_run,
    #         config_path=config_path,
    #     )
    # except Exception as error:
    #     if repr(error) == "exit":
    #         return
    # if is_scheduled_run:
    #     config = get_loaded_config()
    #     email_on = config.notifications.email_on
    #     system_on = config.notifications.system_on
    #     if email_on or system_on:
    #         subject = "ERROR"
    #         contents = str(error)
    #         if email_on:
    #             send_email(subject, contents)
    #         if system_on:
    #             notify(contents, title=get_app_name())
    # print_with_theme(str(error), level=StyleLevel.ERROR)


@app.command()
def reformat(
    *,
    remove_bracketed_years: bool | None = None,
    remove_bracketed_instruments: bool | None = None,
    expand_abbreviations: bool | None = None,
):
    """
    Reformat metadata.

    Rules:

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
    # reformat_settings = cast(ReformatConfig, get_loaded_config().reformat)
    # if remove_bracketed_years is None:
    #     remove_bracketed_years_value = reformat_settings.remove_bracketed_years
    # else:
    #     remove_bracketed_years_value = True
    # if remove_bracketed_instruments is None:
    #     remove_bracketed_instruments_value = (
    #         reformat_settings.remove_bracketed_instruments
    #     )
    # else:
    #     remove_bracketed_instruments_value = True
    # if expand_abbreviations is None:
    #     expand_abbreviations_value = reformat_settings.expand_abbreviations
    # else:
    #     expand_abbreviations_value = True
    # reformat_albums(
    #     remove_bracketed_years_value,
    #     remove_bracketed_instruments_value,
    #     expand_abbreviations_value,
    # )
    print(
        Toml(
            get_config_path(), use_commands_as_keys=False, allow_unknown=True
        ).config
    )
    print(remove_bracketed_years)
