from pathlib import Path

from pytest import MonkeyPatch, mark
from pytest_mock import MockerFixture

from tests.conftest import (
    MockArgV,
    call_command,
    get_command_output,
    get_help_args,
    strip_newlines,
)
from tsundeoku import main
from tsundeoku.config import main as config_main
from tsundeoku.config.config import get_config_path

config_command = "config"


def get_file_system_values() -> str:
    home = Path.home()
    shared_directories = home / "Dropbox"
    return (
        f"shared_directories={{'{shared_directories}'}}\n"
        f"pickle_file={home}/.config/beets/state.pickle\n"
        "ignored_directories=None\n"
        "music_player=Swinsian\n"
    )


def get_import_values() -> str:
    return (
        "reformat=True\n"
        "ask_before_disc_update=False\n"
        "ask_before_artist_update=False\n"
        "allow_prompt=True\n"
    )


def get_reformat_values() -> str:
    return (
        "remove_bracket_years=True\n"
        "remove_bracket_instruments=True\n"
        "expand_abbreviations=True\n"
    )


def get_notifications_values() -> str:
    return "system_on=False\nemail_on=False\nusername=\npassword=\n"


def get_expected_default_config_display() -> str:
    return (
        "[file_system]\n"
        f"{get_file_system_values()}"
        "\n"
        "[import]\n"
        f"{get_import_values()}"
        "\n"
        "[reformat]\n"
        f"{get_reformat_values()}"
        "\n"
        "[notifications]\n"
        f"{get_notifications_values()}"
    )


def get_custom_directories(name: str, create=True) -> Path:
    custom_directories = Path.home() / name
    if create:
        Path.mkdir(custom_directories)
    return custom_directories


def get_custom_shared_directories(create=True) -> Path:
    return get_custom_directories("Custom", create=create)


def get_custom_pickle_file() -> Path:
    return Path.home() / "custom.pickle"


def get_custom_ignored_directories(create=True) -> Path:
    return get_custom_directories("Ignored", create=create)


def get_custom_music_player() -> str:
    return "Custom"


def get_custom_config() -> str:
    custom_shared_directories = get_custom_shared_directories()
    custom_pickle_file = get_custom_pickle_file()
    custom_ignored_directory = get_custom_ignored_directories()
    custom_music_player = get_custom_music_player()
    custom_pickle_file.touch()
    custom_file_system = (
        f'shared_directories = ["{custom_shared_directories}",]\n'
        f'pickle_file = "{custom_pickle_file}"\n'
        f'ignored_directories = ["{custom_ignored_directory}",]\n'
        f'music_player = "{custom_music_player}"\n'
    )
    custom_import = (
        "reformt = false\n"
        "ask_before_disc_update = true\n"
        "ask_before_artist_update = true\n"
        "allow_prompt = false\n"
    )
    custom_reformat = (
        "remove_bracket_years = false\n"
        "remove_bracket_instruments = false\n"
        "expand_abbreviations = false\n"
    )
    custom_notifications = (
        "system_on = true\n"
        "email_on = true\n"
        'username = "username"\n'
        'password = "password"\n'
    )
    return (
        "[file_system]\n"
        f"{custom_file_system}"
        "\n"
        "[import]\n"
        f"{custom_import}"
        "\n"
        "[reformat]\n"
        f"{custom_reformat}"
        "\n"
        "[notifications]\n"
        f"{custom_notifications}"
    )


def get_custom_file_system_values() -> str:
    custom_shared_directories = get_custom_shared_directories(create=False)
    custom_pickle_file = get_custom_pickle_file()
    custom_ignored_directories = get_custom_ignored_directories(create=False)
    custom_music_player = get_custom_music_player()
    return (
        f"shared_directories={{'{custom_shared_directories}'}}\n"
        f"pickle_file={custom_pickle_file}\n"
        f"ignored_directories={{'{custom_ignored_directories}'}}\n"
        f"music_player={custom_music_player}\n"
    )


def get_custom_notifications_values() -> str:
    return "system_on=True\nemail_on=True\nusername=username\npassword=********"


def get_expected_custom_config_display() -> str:
    return (
        "[file_system]\n"
        f"{get_custom_file_system_values()}"
        "\n"
        "[import]\n"
        f"{get_import_values()}"
        "\n"
        "[reformat]\n"
        f"{get_reformat_values()}"
        "\n"
        "[notifications]\n"
        f"{get_custom_notifications_values()}"
    )


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_help(arg: str, mock_get_argv: MockArgV, monkeypatch: MonkeyPatch):
    config_help_text = "Show [default] and set config values."
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = get_command_output([config_command, arg])
    assert config_help_text in output


def test_config():
    output = get_command_output([config_command])
    expected_config_display = get_expected_default_config_display()
    output = strip_newlines(output)
    expected_config_display = strip_newlines(expected_config_display)
    assert output == expected_config_display


def test_config_path():
    output = get_command_output([config_command, "--path"])
    home = str(Path.home())
    output = strip_newlines(output)
    config_path = ".config/tsundeoku/tsundeoku.toml"
    assert home in output and config_path in output


def test_config_file(monkeypatch: MonkeyPatch, mocker: MockerFixture):
    def mock_launch(url: str, locate: bool):
        return url, locate

    monkeypatch.setattr(config_main, "launch", mock_launch)
    spy = mocker.spy(config_main, "launch")
    call_command([config_command, "--file"])
    config_path = str(get_config_path())
    spy.assert_called_once_with(config_path, locate=True)


def test_config_edit(monkeypatch: MonkeyPatch, mocker: MockerFixture):
    def mock_run(args: list[str]):
        return args

    monkeypatch.setattr(config_main, "run", mock_run)
    monkeypatch.setattr(config_main, "environ", {})
    spy = mocker.spy(config_main, "run")
    call_command([config_command, "--edit"])
    config_path = get_config_path()
    spy.assert_called_once_with(["vim", config_path])


def set_confirm_reset(monkeypatch: MonkeyPatch, yes=True):
    def mock_confirm_reset(commands=False) -> bool:
        return yes

    monkeypatch.setattr(config_main, "confirm_reset", mock_confirm_reset)


def set_custom_config_and_get_default_output() -> str:
    default_output = get_command_output([config_command])
    config_path = get_config_path()
    custom_config = get_custom_config()
    config_path.write_text(custom_config)
    output = get_command_output([config_command])
    assert output != default_output
    return default_output


def test_config_reset_all_restores_default_config(monkeypatch: MonkeyPatch):
    set_confirm_reset(monkeypatch)
    default_output = set_custom_config_and_get_default_output()
    output = get_command_output([config_command, "--reset-all"])
    assert output == default_output


def test_config_reset_all_false_keeps_custom_config(monkeypatch: MonkeyPatch):
    set_confirm_reset(monkeypatch, yes=False)
    default_output = set_custom_config_and_get_default_output()
    output = get_command_output([config_command, "--reset-all"])
    assert output != default_output


def test_config_reset_commands_restores_default_options(monkeypatch: MonkeyPatch):
    set_confirm_reset(monkeypatch)
    set_custom_config_and_get_default_output()
    expected_custom_config_display = get_expected_custom_config_display()
    output = get_command_output([config_command, "--reset-commands"])
    expected_custom_config_display = strip_newlines(expected_custom_config_display)
    output = strip_newlines(output)
    assert output == expected_custom_config_display


def test_config_reset_commands_false_keeps_custom_config(monkeypatch: MonkeyPatch):
    set_confirm_reset(monkeypatch, yes=False)
    default_output = set_custom_config_and_get_default_output()
    output = get_command_output([config_command, "--reset-commands"])
    assert output != default_output
