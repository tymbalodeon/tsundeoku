from pytest import MonkeyPatch, mark
from test_config import call_command, config_command, get_import_values

from tests.conftest import MockArgV, get_command_output, get_help_args
from tsundeoku import main
from tsundeoku.config.config import get_loaded_config

import_command = "import"


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_import_help(
    arg: str, mock_get_argv: MockArgV, monkeypatch: MonkeyPatch
):
    config_help_text = 'Show and set default values for "import" command.'
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output(["config", import_command, arg])
    assert config_help_text in output


def test_config_import():
    output = get_command_output([config_command, import_command])
    assert output == get_import_values()


def get_config_reformat():
    return get_loaded_config().import_new.reformat


def test_import_reformat():
    default_reformat = get_config_reformat()
    call_command([config_command, import_command, "--as-is"])
    output = get_command_output([config_command, import_command, "--reformat"])
    updated_reformat = get_config_reformat()
    assert output == get_import_values()
    assert updated_reformat == default_reformat
    assert updated_reformat is True


def test_import_as_is():
    default_reformat = get_config_reformat()
    output = get_command_output([config_command, import_command, "--as-is"])
    updated_reformat = get_config_reformat()
    assert output != get_import_values()
    assert updated_reformat != default_reformat
    assert updated_reformat is False


def get_config_ask_before_disc_update():
    return get_loaded_config().import_new.ask_before_disc_update


def test_import_ask_before_disc_update():
    default_ask_before_disc_update = get_config_ask_before_disc_update()
    output = get_command_output(
        [config_command, import_command, "--ask-before-disc-update"]
    )
    updated_ask_before_disc_update = get_config_ask_before_disc_update()
    assert output != get_import_values()
    assert updated_ask_before_disc_update != default_ask_before_disc_update
    assert updated_ask_before_disc_update is True


def test_import_auto_update_disc():
    default_ask_before_disc_update = get_config_ask_before_disc_update()
    call_command([config_command, import_command, "--ask-before-disc-update"])
    output = get_command_output([config_command, import_command, "--auto-update-disc"])
    updated_ask_before_disc_update = get_config_ask_before_disc_update()
    assert output == get_import_values()
    assert updated_ask_before_disc_update == default_ask_before_disc_update
    assert updated_ask_before_disc_update is False


def get_config_ask_before_artist_update():
    return get_loaded_config().import_new.ask_before_artist_update


def test_import_ask_before_artist_update():
    default_ask_before_artist_update = get_config_ask_before_artist_update()
    output = get_command_output(
        [config_command, import_command, "--ask-before-artist-update"]
    )
    updated_ask_before_artist_update = get_config_ask_before_artist_update()
    assert output != get_import_values()
    assert updated_ask_before_artist_update != default_ask_before_artist_update
    assert updated_ask_before_artist_update is True


def test_import_auto_update_artist():
    default_ask_before_artist_update = get_config_ask_before_artist_update()
    call_command([config_command, import_command, "--ask-before-artist-update"])
    output = get_command_output(
        [config_command, import_command, "--auto-update-artist"]
    )
    updated_ask_before_artist_update = get_config_ask_before_artist_update()
    assert output == get_import_values()
    assert updated_ask_before_artist_update == default_ask_before_artist_update
    assert updated_ask_before_artist_update is False


def get_config_allow_prompt():
    return get_loaded_config().import_new.allow_prompt


def test_import_allow_prompt():
    default_allow_prompt = get_config_allow_prompt()
    call_command([config_command, import_command, "--disallow-prompt"])
    output = get_command_output([config_command, import_command, "--allow-prompt"])
    updated_allow_prompt = get_config_allow_prompt()
    assert output == get_import_values()
    assert updated_allow_prompt == default_allow_prompt
    assert updated_allow_prompt is True


def test_import_disallow_prompt():
    default_allow_prompt = get_config_allow_prompt()
    output = get_command_output([config_command, import_command, "--disallow-prompt"])
    updated_allow_prompt = get_config_allow_prompt()
    assert output != get_import_values()
    assert updated_allow_prompt != default_allow_prompt
    assert updated_allow_prompt is False
