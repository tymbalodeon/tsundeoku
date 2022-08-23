from typer.testing import CliRunner

from musicbros.main import app

CLI_RUNNER = CliRunner()


def test_import_new_help():
    import_new_help_text = (
        'Copy new adds from your shared folder to your "beets" library'
    )
    result = CLI_RUNNER.invoke(app, ["import-new", "-h"])
    assert import_new_help_text in result.stdout
    assert result.exit_code == 0
