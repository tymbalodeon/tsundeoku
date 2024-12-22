import re
from dataclasses import asdict, dataclass, field
from os import environ
from pathlib import Path
from subprocess import run
from typing import Annotated, Literal

import toml
from cyclopts import App, Group, Parameter
from cyclopts.config import Toml
from rich import print
from rich.syntax import Syntax

config_app = App(
    name="config",
    help="Show and set config values",
    version_flags=(),
)


# TODO is there a better place to store this name?
def get_app_name() -> Literal["tsundeoku"]:
    return "tsundeoku"


def set_default_config(path: Path | None):
    if path is None:
        path = get_config_path()
    path.write_text(Config().to_toml())


def get_config_path() -> Path:
    app_name = get_app_name()
    return Path.home() / f".config/{app_name}/{app_name}.toml"


@dataclass
class Files:
    shared_directories: Annotated[set[Path], Parameter(negative=())] = field(
        default_factory=lambda: {Path.home() / "Dropbox"}
    )
    ignored_directories: Annotated[set[Path], Parameter(negative=())] = field(
        default_factory=set
    )


@dataclass
class Import:
    allow_prompt: Annotated[bool, Parameter(negative=())] = False
    ask_before_artist_update: Annotated[bool, Parameter(negative=())] = True
    ask_before_disc_update: Annotated[bool, Parameter(negative=())] = True
    reformat: Annotated[bool, Parameter(negative=())] = False


@dataclass
class Notifications:
    email_on: Annotated[bool, Parameter(negative=())] = False
    system_on: Annotated[bool, Parameter(negative=())] = False
    username: str | None = ""
    password: str | None = ""


@dataclass
class Reformat:
    expand_abbreviations: Annotated[bool, Parameter(negative=())] = False
    remove_bracketed_instruments: Annotated[bool, Parameter(negative=())] = (
        False
    )
    remove_bracketed_years: Annotated[bool, Parameter(negative=())] = False


@dataclass
class Config:
    files: Files = field(default_factory=lambda: Files())
    import_config: Import = field(default_factory=lambda: Import())
    notifications: Notifications = field(
        default_factory=lambda: Notifications()
    )
    reformat: Reformat = field(default_factory=lambda: Reformat())

    @staticmethod
    def to_str(paths: set[Path]) -> set[str]:
        return {str(path) for path in paths}

    @staticmethod
    def from_toml(path: Path | None = None) -> "Config":
        if path is None:
            path = get_config_path()
        config = Toml(path).config
        config["import_config"] = config.pop("import")
        config["files"] = config.pop("file_system")
        config["files"].pop("music_player")
        config["files"].pop("pickle_file")
        return Config(**config)

    def to_toml(self) -> str:
        items = asdict(self)
        files = items["files"]
        files["shared_directories"] = self.to_str(files["shared_directories"])
        files["ignored_directories"] = self.to_str(
            files["ignored_directories"]
        )
        return toml.dumps(items)


@config_app.command
def edit():
    """Open config file in $EDITOR"""
    run([environ.get("EDITOR", "vim"), get_config_path()])


@config_app.command
def path():
    """Show config file path"""
    print(get_config_path())


global_group = Group("Global", sort_key=0)


@config_app.command(name="set")
def set_config_value(
    *,
    files: Annotated[Files | None, Parameter(group="Files")] = None,
    import_config: Annotated[
        Import | None, Parameter(name="import", group="Import")
    ] = None,
    notifications: Annotated[
        Notifications | None, Parameter(group="Notifications")
    ] = None,
    reformat: Annotated[Reformat | None, Parameter(group="Reformat")] = None,
    restore_defaults: Annotated[bool, Parameter(group=global_group)] = False,
):
    """Set config values"""
    if restore_defaults:
        set_default_config(get_config_path())
        return
    print(import_config)
    print(notifications)
    print(reformat)


# TODO
# display defaults if missing from config file
@config_app.command
def show(
    *,
    files: Annotated[Files | None, Parameter(group="Files")] = None,
    import_config: Annotated[
        Import | None, Parameter(name="import", group="Import")
    ] = None,
    notifications: Annotated[
        Notifications | None, Parameter(group="Notifications")
    ] = None,
    reformat: Annotated[Reformat | None, Parameter(group="Reformat")] = None,
    default: Annotated[bool, Parameter(group=global_group)] = False,
    show_secrets: Annotated[bool, Parameter(group=global_group)] = False,
):
    """
    Show config values

    Parameters
    ----------
    default: bool
        Show default value(s)
    show_secrets: bool
        Show secret config values
    """
    if default:
        config = Config().to_toml()
    else:
        config_path = get_config_path()
        if not config_path.exists():
            return
        config = config_path.read_text()
        if not show_secrets:
            # TODO use capture groups
            config = re.sub('password = ".+"', 'password = "********"', config)
    # TODO
    # implement selectors for specific values
    print(Syntax(config, "toml", theme="ansi_dark"))
