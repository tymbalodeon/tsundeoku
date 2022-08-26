from pathlib import Path

from typer.testing import CliRunner

from tests.mocks import set_mock_home
from tsundeoku import config
from tsundeoku.config import (
    get_config_directory,
    get_config_file,
    get_config_options,
    get_config_path,
    get_directory_display,
    get_ignored_directories,
    get_option_and_value,
    get_shared_directories,
    validate_music_player,
)
from tsundeoku.main import app


def test_get_config_directory(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    config_directory = Path.home() / ".config/tsundeoku"
    assert not config_directory.exists()
    config_directory = get_config_directory()
    assert config_directory.exists()


def get_mock_shared_directory() -> str:
    shared_directory = str(Path.home() / "Dropbox")
    return f'["{shared_directory}"]'


def get_mock_pickle_file() -> Path:
    return Path.home() / ".config/beets/state.pickle"


def get_options_and_vaues(default=True) -> list[tuple]:
    shared_directory = get_mock_shared_directory()
    pickle_file = str(get_mock_pickle_file())
    if default:
        ignored_directories = "[]"
        music_player = "Swinsian"
    else:
        ignored_directories = '["/bad_directory"]'
        music_player = "Not An App"
    return [
        ("shared_directory", shared_directory),
        ("pickle_file", pickle_file),
        ("ignored_directories", ignored_directories),
        ("music_player", music_player),
    ]


def format_options_and_values(default=True) -> str:
    options_and_values = get_options_and_vaues(default)
    config_lines = [f"{option} = {value}" for option, value in options_and_values]
    return "\n".join(config_lines)


def get_mock_config(default=True) -> str:
    options_and_values = format_options_and_values(default)
    return f"[tsundeoku]\n{options_and_values}\n"


def test_get_config_file(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    config_directory = get_config_directory()
    config_file = config_directory / "tsundeoku.ini"
    assert not config_file.exists()
    config_file = get_config_file()
    assert config_file.exists()
    config = config_file.read_text()
    expected_config_values = format_options_and_values(tmp_path)
    assert config == f"[tsundeoku]\n{expected_config_values}\n"


def check_option_and_value(expected_option: str, expected_value: str):
    option, value = get_option_and_value(expected_option)
    assert option == expected_option
    assert value == expected_value


def test_option_and_value_defaults(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    expected_options_and_values = get_options_and_vaues()
    for expected_option, expected_value in expected_options_and_values:
        check_option_and_value(expected_option, expected_value)


def test_get_config_options(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    actual_options_and_values = get_config_options()
    expected_options_and_values = get_options_and_vaues()
    actual_and_expected = zip(actual_options_and_values, expected_options_and_values)
    assert all(actual == expected for actual, expected in actual_and_expected)


def mock_get_config_value(_):
    return None


def test_get_shared_directories(monkeypatch):
    monkeypatch.setattr(config, "get_config_value", mock_get_config_value)
    ignored_directories = get_shared_directories()
    assert ignored_directories == []


def test_get_ignored_directories(monkeypatch):
    monkeypatch.setattr(config, "get_config_value", mock_get_config_value)
    ignored_directories = get_ignored_directories()
    assert ignored_directories == []


def test_get_directory_display():
    directory_display = get_directory_display(None)
    assert directory_display == ""


def test_config_help():
    config_help_text = (
        "Display config [default], display config path, edit config file in $EDITOR"
    )
    result = CliRunner().invoke(app, ["config", "-h"])
    assert config_help_text in result.output
    assert result.exit_code == 0


def mock_application_exists(command: str) -> bool:
    if "Swinsian" in command:
        return True
    return False


def mock_get_music_player():
    return None


def test_validate_music_player(monkeypatch):
    monkeypatch.setattr(config, "get_music_player", mock_get_music_player)
    error_message = validate_music_player()
    assert error_message and "WARNING" in error_message


def test_bad_config(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "application_exists", mock_application_exists)
    config_path = get_config_path()
    bad_config_values = get_mock_config(default=False)
    config_path.write_text(bad_config_values)
    result = CliRunner().invoke(app, "config")
    output = result.output
    assert "WARNING" in output
    assert result.exit_code == 0


def test_good_config(monkeypatch, tmp_path):
    set_mock_home(monkeypatch, tmp_path)
    monkeypatch.setattr(config, "application_exists", mock_application_exists)
    shared_directory = tmp_path / "Dropbox"
    Path.mkdir(shared_directory)
    pickle_file = get_mock_pickle_file()
    Path.mkdir(pickle_file.parent, parents=True)
    pickle_file.touch()
    result = CliRunner().invoke(app, "config")
    output = result.output
    assert "WARNING" not in output
    assert result.exit_code == 0
