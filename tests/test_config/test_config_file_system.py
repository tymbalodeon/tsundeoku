from pathlib import Path

from pytest import mark
from test_config import (
    config_command,
    get_custom_ignored_directories,
    get_custom_music_player,
    get_custom_pickle_file,
    get_custom_shared_directories,
    get_file_system_values,
)

from tests.conftest import get_command_output, get_help_args, strip_newlines
from tsundeoku import main
from tsundeoku.config import main as config_main


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_file_system_help(arg, mock_get_argv, monkeypatch):
    config_help_text = "Show and set values for the file-system."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output(["config", "file-system", arg])
    assert config_help_text in output


def test_file_system():
    output = get_command_output([config_command, "file-system"])
    expected_file_system_values = get_file_system_values()
    output = strip_newlines(output)
    expected_file_system_values = strip_newlines(expected_file_system_values)
    assert output == expected_file_system_values


def set_confirm_update(monkeypatch, yes=True):
    def mock_confirm_update(value: list[str] | str, add=False, remove=False) -> bool:
        return yes

    monkeypatch.setattr(config_main, "confirm_update", mock_confirm_update)


def test_file_system_shared_directories_good_value_updates_config(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_shared_directories = get_custom_shared_directories()
    Path.mkdir(custom_shared_directories)
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--shared-directories",
            str(custom_shared_directories),
        ]
    )
    home = Path.home()
    expected_updated_config = (
        f"shared_directories={{'{custom_shared_directories}'}}\n"
        f"pickle_file={home}/.config/beets/state.pickle\n"
        "ignored_directories=None\n"
        "music_player=Swinsian\n"
    )
    output = strip_newlines(output)
    expected_updated_config = strip_newlines(expected_updated_config)
    assert output == expected_updated_config


def test_file_system_shared_directories_good_value_false_keeps_config(monkeypatch):
    set_confirm_update(monkeypatch, yes=False)
    custom_shared_directories = get_custom_shared_directories()
    Path.mkdir(custom_shared_directories)
    default_output = get_command_output([config_command, "file-system"])
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--shared-directories",
            str(custom_shared_directories),
        ]
    )
    assert output == default_output


def test_file_system_shared_directories_bad_value_shows_error(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_shared_directories = get_custom_shared_directories()
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--shared-directories",
            str(custom_shared_directories),
        ]
    )
    error_message = (
        f'ERROR: file or directory at path "{custom_shared_directories}" does not'
        " exist\n\n"
    )
    output = strip_newlines(output)
    error_message = strip_newlines(error_message)
    assert output == error_message


def test_file_system_pickle_file_good_value_updates_config(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_pickle_file = get_custom_pickle_file()
    custom_pickle_file.touch()
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--pickle-file",
            str(custom_pickle_file),
        ]
    )
    home = Path.home()
    shared_directories = home / "Dropbox"
    expected_updated_config = (
        f"shared_directories={{'{shared_directories}'}}\n"
        f"pickle_file={custom_pickle_file}\n"
        "ignored_directories=None\n"
        "music_player=Swinsian\n"
    )
    output = strip_newlines(output)
    expected_updated_config = strip_newlines(expected_updated_config)
    assert output == expected_updated_config


def test_file_system_pickle_file_good_value_false_keeps_config(monkeypatch):
    set_confirm_update(monkeypatch, yes=False)
    custom_pickle_file = get_custom_pickle_file()
    custom_pickle_file.touch()
    default_output = get_command_output([config_command, "file-system"])
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--pickle-file",
            str(custom_pickle_file),
        ]
    )
    assert output == default_output


def test_file_system_pickle_file_bad_value_shows_error(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_pickle_file = get_custom_pickle_file()
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--pickle-file",
            str(custom_pickle_file),
        ]
    )
    error_message = (
        f'ERROR: file or directory at path "{custom_pickle_file}" does not exist\n\n'
    )
    output = strip_newlines(output)
    error_message = strip_newlines(error_message)
    assert output == error_message


def test_file_system_ignored_directories_good_value_updates_config(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_ignored_directories = get_custom_ignored_directories()
    Path.mkdir(custom_ignored_directories)
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--ignored-directories",
            str(custom_ignored_directories),
        ]
    )
    home = Path.home()
    shared_directories = home / "Dropbox"
    expected_updated_config = (
        f"shared_directories={{'{shared_directories}'}}\n"
        f"pickle_file={home}/.config/beets/state.pickle\n"
        f"ignored_directories={{'{custom_ignored_directories}'}}\n"
        "music_player=Swinsian\n"
    )
    output = strip_newlines(output)
    expected_updated_config = strip_newlines(expected_updated_config)
    assert output == expected_updated_config


def test_file_system_ignored_directories_good_value_false_keeps_config(monkeypatch):
    set_confirm_update(monkeypatch, yes=False)
    custom_ignored_directories = get_custom_ignored_directories()
    Path.mkdir(custom_ignored_directories)
    default_output = get_command_output([config_command, "file-system"])
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--ignored-directories",
            str(custom_ignored_directories),
        ]
    )
    assert output == default_output


def test_file_system_ignored_directories_bad_value_shows_error(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_ignored_directories = get_custom_ignored_directories()
    output = get_command_output(
        [
            config_command,
            "file-system",
            "--ignored-directories",
            str(custom_ignored_directories),
        ]
    )
    error_message = (
        f'ERROR: file or directory at path "{custom_ignored_directories}" does not'
        " exist\n\n"
    )
    output = strip_newlines(output)
    error_message = strip_newlines(error_message)
    assert output == error_message


def test_file_system_music_player_good_value_updates_config(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_music_player = get_custom_music_player()
    output = get_command_output(
        [config_command, "file-system", "--music-player", custom_music_player]
    )
    home = Path.home()
    shared_directories = home / "Dropbox"
    expected_updated_config = (
        f"shared_directories={{'{shared_directories}'}}\n"
        f"pickle_file={home}/.config/beets/state.pickle\n"
        "ignored_directories=None\n"
        f"music_player={custom_music_player}\n"
    )
    output = strip_newlines(output)
    expected_updated_config = strip_newlines(expected_updated_config)
    assert output == expected_updated_config


def test_file_system_music_player_good_value_false_keeps_config(monkeypatch):
    set_confirm_update(monkeypatch, yes=False)
    custom_music_player = get_custom_music_player()
    default_output = get_command_output([config_command, "file-system"])
    output = get_command_output(
        [config_command, "file-system", "--music-player", custom_music_player]
    )
    assert output == default_output


def test_file_system_music_player_bad_value_shows_error(monkeypatch):
    set_confirm_update(monkeypatch)
    custom_music_player = "NotAnApplication"
    output = get_command_output(
        [config_command, "file-system", "--music-player", custom_music_player]
    )
    error_message = 'ERROR: application "NotAnApplication" not found'
    output = strip_newlines(output)
    error_message = strip_newlines(error_message)
    assert output == error_message
