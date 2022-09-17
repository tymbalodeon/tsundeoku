from pytest import mark
from test_config import config_command, get_reformat_values

from tests.conftest import call_command, get_command_output, get_help_args
from tsundeoku import main
from tsundeoku.config.config import get_loaded_config

reformat_command = "reformat"


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_reformat_help(arg, mock_get_argv, monkeypatch):
    config_help_text = 'Show and set default values for "reformat" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([config_command, reformat_command, arg])
    assert config_help_text in output


def test_config_reformat():
    output = get_command_output([config_command, reformat_command])
    assert output == get_reformat_values()


def get_config_remove_bracket_years():
    return get_loaded_config().reformat.remove_bracket_years


def test_reformat_remove_bracket_years():
    default_remove_bracket_years = get_config_remove_bracket_years()
    call_command([config_command, reformat_command, "--years-as-is"])
    output = get_command_output(
        [config_command, reformat_command, "--remove-bracket-years"]
    )
    updated_remove_bracket_years = get_config_remove_bracket_years()
    assert output == get_reformat_values()
    assert updated_remove_bracket_years == default_remove_bracket_years
    assert updated_remove_bracket_years is True


def test_reformat_years_as_is():
    default_remove_bracket_years = get_config_remove_bracket_years()
    output = get_command_output([config_command, reformat_command, "--years-as-is"])
    updated_remove_bracket_years = get_config_remove_bracket_years()
    assert output != get_reformat_values()
    assert updated_remove_bracket_years != default_remove_bracket_years
    assert updated_remove_bracket_years is False


def get_config_remove_bracket_instruments():
    return get_loaded_config().reformat.remove_bracket_instruments


def test_reformat_remove_bracket_instruments():
    default_remove_bracket_instruments = get_config_remove_bracket_instruments()
    call_command([config_command, reformat_command, "--instruments-as-is"])
    output = get_command_output(
        [config_command, reformat_command, "--remove-bracket-instruments"]
    )
    updated_remove_bracket_instruments = get_config_remove_bracket_instruments()
    assert output == get_reformat_values()
    assert updated_remove_bracket_instruments == default_remove_bracket_instruments
    assert updated_remove_bracket_instruments is True


def test_reformat_instruments_as_is():
    default_remove_bracket_instruments = get_config_remove_bracket_instruments()
    output = get_command_output(
        [config_command, reformat_command, "--instruments-as-is"]
    )
    updated_remove_bracket_instruments = get_config_remove_bracket_instruments()
    assert output != get_reformat_values()
    assert updated_remove_bracket_instruments != default_remove_bracket_instruments
    assert updated_remove_bracket_instruments is False


def get_config_expand_abbreviations():
    return get_loaded_config().reformat.expand_abbreviations


def test_reformat_expand_abbreviations():
    default_expand_abbreviations = get_config_expand_abbreviations()
    call_command([config_command, reformat_command, "--abbreviations-as-is"])
    output = get_command_output(
        [config_command, reformat_command, "--expand-abbreviations"]
    )
    updated_expand_abbreviations = get_config_expand_abbreviations()
    assert output == get_reformat_values()
    assert updated_expand_abbreviations == default_expand_abbreviations
    assert updated_expand_abbreviations is True


def test_reformat_abbreviations_as_is():
    default_expand_abbreviations = get_config_expand_abbreviations()
    output = get_command_output(
        [config_command, reformat_command, "--abbreviations-as-is"]
    )
    updated_expand_abbreviations = get_config_expand_abbreviations()
    assert output != get_reformat_values()
    assert updated_expand_abbreviations != default_expand_abbreviations
    assert updated_expand_abbreviations is False
