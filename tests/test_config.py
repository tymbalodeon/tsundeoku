from typer.testing import CliRunner

from tsundeoku.main import tsundeoku


def test_config_help():
    config_help_text = "Show [default] and set config values."
    result = CliRunner().invoke(tsundeoku, ["config", "-h"])
    assert config_help_text in result.output
