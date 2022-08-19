from typer.testing import CliRunner

from musicbros import __version__
from musicbros.main import app
from musicbros.style import format_int_with_commas

CLI_RUNNER = CliRunner()


def test_version():
    expected_version = "0.3.0"
    expected_version_display = f"musicbros {expected_version}\n"
    assert __version__ == expected_version
    for option in ["--version", "-V"]:
        result = CLI_RUNNER.invoke(app, option)
        assert result.stdout == expected_version_display
        assert result.exit_code == 0


def test_help():
    app_description = (
        'CLI for managing imports from a shared folder to a "beets" library'
    )
    for option in ["--help", "-h"]:
        result = CLI_RUNNER.invoke(app, option)
        assert app_description in result.stdout
        assert result.exit_code == 0


def test_config_help():
    config_help_text = "Create, update, and display config values"
    result = CLI_RUNNER.invoke(app, ["config", "-h"])
    assert config_help_text in result.stdout
    assert result.exit_code == 0


def test_config():
    result = CLI_RUNNER.invoke(app, "config")
    section = "[musicbros]"
    stdout = result.stdout
    assert section in stdout
    options = ["shared_directory", "pickle_file", "ignored_directories", "music_player"]
    for option in options:
        option = f"{option} = "
        assert option in stdout
    assert result.exit_code == 0


def test_style_int():
    one_thousand = 1000
    expected_formatting = "1,000"
    one_thousand_with_comma = format_int_with_commas(one_thousand)
    assert one_thousand_with_comma == expected_formatting


def test_import_new_help():
    import_new_help_text = (
        'Copy new adds from your shared folder to your "beets" library'
    )
    result = CLI_RUNNER.invoke(app, ["import-new", "-h"])
    assert import_new_help_text in result.stdout
    assert result.exit_code == 0


def test_update_metadata_help():
    update_metadata_help_text = "Update metadata according to the following rules:"
    remove_bracket_year_help_text = (
        'Remove bracketed years (e.g., "[2022]") from album fields'
    )
    expand_abbreviation_help_text = (
        'Expand the abbreviations "Rec.," "Rec.s," and "Orig." to "Recording,"'
    )
    remove_bracket_solo_help_text = (
        "[Optional] Remove bracketed solo instrument indications"
    )
    result = CLI_RUNNER.invoke(app, ["update-metadata", "-h"])
    stdout = result.stdout
    for help_text in [
        update_metadata_help_text,
        remove_bracket_year_help_text,
        expand_abbreviation_help_text,
        remove_bracket_solo_help_text,
    ]:
        assert help_text in stdout
    assert result.exit_code == 0
