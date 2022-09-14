from pytest import mark
from typer.testing import CliRunner

from tsundeoku.main import tsundeoku

config_help_text = "Show [default] and set config values."


@mark.parametrize(
    "arg, config_help_text", [("--help", config_help_text), ("-h", config_help_text)]
)
def test_config_help(arg, config_help_text):
    result = CliRunner().invoke(tsundeoku, ["config", arg])
    assert config_help_text in result.output
