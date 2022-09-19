from pytest import MonkeyPatch, fixture, mark

from tsundeoku import main
from tests.test_config.test_config import config_command

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


@fixture
def set_custom_config():
    call_command([config_command, reformat_command, "--years-as-is"])
    call_command([config_command, reformat_command, "--instruments-as-is"])
    call_command([config_command, reformat_command, "--abbreviations-as-is"])


remove_bracket_years_text = 'Removing bracketed years from all "album" tags...'
remove_bracket_instruments_text = (
    'Removing bracketed solo instrument indications from all "artist" tags...'
)
expand_abbreviations_text = [
    'Replacing "Rec." with "Recording" in all "album" tags...',
    'Replacing "Recs" with "Recordings" in all "album" tags...',
    'Replacing "Orig." with "Original" in all "album" tags...',
    'Replacing "Ed." with "Edition" in all "album" tags...',
]


def get_all_reformat_texts() -> list[str]:
    return [
        remove_bracket_years_text,
        remove_bracket_instruments_text,
    ] + expand_abbreviations_text


@mark.parametrize("text", get_all_reformat_texts())
def test_reformat_default(text: str):
    output = call_command([reformat_command])
    assert text in output


def test_reformat_config_years_as_is(set_custom_config):
    output = call_command([reformat_command])
    assert remove_bracket_years_text not in output


def test_reformat_years_as_is():
    output = call_command([reformat_command, "--years-as-is"])
    assert remove_bracket_years_text not in output


def test_remove_bracket_years_default():
    output = call_command([reformat_command, "--remove-bracket-years"])
    assert remove_bracket_years_text in output


def test_remove_bracket_years_config(set_custom_config):
    output = call_command([reformat_command, "--remove-bracket-years"])
    assert remove_bracket_years_text in output


def test_reformat_config_instruments_as_is(set_custom_config):
    output = call_command([reformat_command])
    assert remove_bracket_instruments_text not in output


def test_reformat_instruments_as_is():
    output = call_command([reformat_command, "--instruments-as-is"])
    assert remove_bracket_instruments_text not in output


def test_remove_bracket_instruments_default():
    output = call_command([reformat_command, "--remove-bracket-instruments"])
    assert remove_bracket_instruments_text in output


def test_remove_bracket_instruments_config(set_custom_config):
    output = call_command([reformat_command, "--remove-bracket-instruments"])
    assert remove_bracket_instruments_text in output


@mark.parametrize("text", expand_abbreviations_text)
def test_reformat_config_abbreviations_as_is(text: str, set_custom_config):
    output = call_command([reformat_command])
    assert text not in output


@mark.parametrize("text", expand_abbreviations_text)
def test_reformat_abbreviations_as_is(text: str):
    output = call_command([reformat_command, "--abbreviations-as-is"])
    assert text not in output


@mark.parametrize("text", expand_abbreviations_text)
def test_expand_abbreviations_default(text: str):
    output = call_command([reformat_command, "--expand-abbreviations"])
    assert text in output


@mark.parametrize("text", expand_abbreviations_text)
def test_expand_abbreviations_config(text: str, set_custom_config):
    output = call_command([reformat_command, "--expand-abbreviations"])
    assert text in output
