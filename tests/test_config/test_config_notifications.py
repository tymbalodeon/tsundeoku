from pytest import MonkeyPatch, mark
from test_config import config_command, get_notifications_values

from tests.conftest import MockArgV, call_command, get_help_args
from tsundeoku import main
from tsundeoku.config.config import get_loaded_config

notifications_command = "notifications"


@mark.parametrize("arg, mock_get_argv", get_help_args())
def test_config_notifications_help(
    arg: str, mock_get_argv: MockArgV, monkeypatch: MonkeyPatch
):
    config_help_text = (
        "Show and set values for notifications from scheduled import command."
    )
    monkeypatch.setattr(main, "get_argv", mock_get_argv)
    output = call_command([config_command, notifications_command, arg])
    assert config_help_text in output


def test_config_notifications():
    output = call_command([config_command, notifications_command])
    assert output == get_notifications_values()


def get_config_username():
    return get_loaded_config().notifications.username


def test_notifications_username():
    default_username = get_config_username()
    username = "username"
    output = call_command([
        config_command, notifications_command, "--username", username
    ])
    updated_username = get_config_username()
    assert output != get_notifications_values()
    assert updated_username != default_username
    assert updated_username == username


def get_config_password():
    return get_loaded_config().notifications.password


def test_notifications_password():
    default_password = get_config_password()
    password = "secret"
    output = call_command([
        config_command, notifications_command, "--password", password
    ])
    updated_password = get_config_password()
    assert output != get_notifications_values()
    assert password not in output
    assert updated_password != default_password
    assert updated_password == password


def get_config_email_on():
    return get_loaded_config().notifications.email_on


def test_notifications_email_on():
    default_email_on = get_config_email_on()
    output = call_command([
        config_command, notifications_command, "--email-on"
    ])
    updated_email_on = get_config_email_on()
    assert output != get_notifications_values()
    assert updated_email_on != default_email_on
    assert updated_email_on is True


def test_notifications_email_off():
    default_email_on = get_config_email_on()
    call_command([config_command, notifications_command, "--email-on"])
    output = call_command([
        config_command, notifications_command, "--email-off"
    ])
    updated_email_on = get_config_email_on()
    assert output == get_notifications_values()
    assert updated_email_on == default_email_on
    assert updated_email_on is False


def get_config_system_on():
    return get_loaded_config().notifications.system_on


def test_notifications_system_on():
    default_system_on = get_config_system_on()
    output = call_command([
        config_command, notifications_command, "--system-on"
    ])
    updated_system_on = get_config_system_on()
    assert output != get_notifications_values()
    assert updated_system_on != default_system_on
    assert updated_system_on is True


def test_notifications_system_off():
    default_system_on = get_config_system_on()
    call_command([config_command, notifications_command, "--system-on"])
    output = call_command([
        config_command, notifications_command, "--system-off"
    ])
    updated_system_on = get_config_system_on()
    assert output == get_notifications_values()
    assert updated_system_on == default_system_on
    assert updated_system_on is False
