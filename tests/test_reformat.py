from pytest import MonkeyPatch, mark

from tsundeoku import main
from tsundeoku.reformat import Action, get_actions
from tsundeoku.regex import (
    BRACKET_YEAR_REGEX,
    EDITION_REGEX,
    ORIGINAL_REGEX,
    RECORDING_REGEX,
    RECORDINGS_REGEX,
    SOLO_INSTRUMENT_REGEX,
)

from .conftest import MockArgV, call_command, get_mock_get_argvs

reformat_command = "reformat"
mock_get_argv_long, mock_get_argv_short = get_mock_get_argvs()
help_texts = [
    "Reformat metadata according to the following rules:",
    'Remove bracketed years (e.g., "[2022]") from album fields',
    'Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"',
    "[Optional] Remove bracketed solo instrument indications",
]


def get_args() -> list[tuple[str, MockArgV, str]]:
    args = []
    for help_text in help_texts:
        args.append(("--help", mock_get_argv_long, help_text))
        args.append(("-h", mock_get_argv_short, help_text))
    return args


@mark.parametrize("arg, mock_get_argv, help_text", get_args())
def test_reformat_help(
    arg: str, mock_get_argv: MockArgV, help_text: str, monkeypatch: MonkeyPatch
):
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = call_command([reformat_command, arg])
    assert help_text in output


def test_get_actions_all_false():
    actions = get_actions(
        remove_bracket_years=False,
        remove_bracket_instruments=False,
        expand_abbreviations=False,
    )
    assert not actions


def test_get_actions_remove_bracket_years():
    actions = get_actions(
        remove_bracket_years=True,
        remove_bracket_instruments=False,
        expand_abbreviations=False,
    )
    remove_bracket_years = Action(
        message='Removing bracketed years from all "album" tags...',
        find=BRACKET_YEAR_REGEX,
        replace="",
    )
    assert remove_bracket_years in actions and len(actions) == 1


def test_get_actions_remove_bracket_instruments():
    actions = get_actions(
        remove_bracket_years=False,
        remove_bracket_instruments=True,
        expand_abbreviations=False,
    )
    remove_bracket_instruments = Action(
        message=(
            'Removing bracketed solo instrument indications from all "artist" tags...'
        ),
        find=SOLO_INSTRUMENT_REGEX,
        replace="",
        tag="artist",
        operate_on_albums=False,
    )
    assert remove_bracket_instruments in actions and len(actions) == 1


expand_abbreviations = [
    Action(
        message='Replacing "Rec." with "Recording" in all "album" tags...',
        find=RECORDING_REGEX,
        replace="Recording",
    ),
    Action(
        message='Replacing "Recs" with "Recordings" in all "album" tags...',
        find=RECORDINGS_REGEX,
        replace="Recordings",
    ),
    Action(
        message='Replacing "Orig." with "Original" in all "album" tags...',
        find=ORIGINAL_REGEX,
        replace="Original",
    ),
    Action(
        message='Replacing "Ed." with "Edition" in all "album" tags...',
        find=EDITION_REGEX,
        replace="Edition",
    ),
]


@mark.parametrize("action", expand_abbreviations)
def test_get_actions_expand_abbreviations(action):
    actions = get_actions(
        remove_bracket_years=False,
        remove_bracket_instruments=False,
        expand_abbreviations=True,
    )
    assert action in actions and len(actions) == 4
