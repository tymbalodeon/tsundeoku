import re
from dataclasses import asdict, dataclass, field
from os import environ
from pathlib import Path
from subprocess import run
from typing import Annotated, Literal, cast

import toml
from cyclopts import App, Group, Parameter
from cyclopts.config import Toml
from rich import print
from rich.syntax import Syntax

config_app = App(
    name="config",
    help="Show and set config values.",
    version_flags=(),
)


@dataclass
class Files:
    shared_directories: Annotated[
        set[Path], Parameter(negative=(), show_default=False)
    ] = field(default_factory=lambda: {Path.home() / "Dropbox"})
    ignored_directories: Annotated[
        set[Path], Parameter(negative=(), show_default=False)
    ] = field(default_factory=set)

    @staticmethod
    def paths_to_str(paths: set[Path]) -> set[str]:
        return {str(path) for path in paths}

    def to_dict(self) -> dict[str, list[str]]:
        items = asdict(self)
        items["shared_directories"] = self.paths_to_str(
            items["shared_directories"]
        )
        items["ignored_directories"] = self.paths_to_str(
            items["ignored_directories"]
        )
        return items


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
    username: str | None = None
    password: str | None = None


@dataclass
class Reformat:
    expand_abbreviations: Annotated[bool, Parameter(negative=())] = False
    remove_bracketed_instruments: Annotated[bool, Parameter(negative=())] = (
        False
    )
    remove_bracketed_years: Annotated[bool, Parameter(negative=())] = False


# TODO is there a better place to store this name?
def get_app_name() -> Literal["tsundeoku"]:
    return "tsundeoku"


def get_config_path() -> Path:
    app_name = get_app_name()
    return Path.home() / f".config/{app_name}/{app_name}.toml"


@dataclass
class Config:
    files: Files = field(default_factory=lambda: Files())
    import_config: Import = field(default_factory=lambda: Import())
    notifications: Notifications = field(
        default_factory=lambda: Notifications()
    )
    reformat: Reformat = field(default_factory=lambda: Reformat())

    @staticmethod
    def from_toml(path: Path | None = None) -> "Config":
        if path is None:
            path = get_config_path()
        config = Toml(path).config
        config["import_config"] = config.pop("import")
        config["files"] = config.pop("file_system")
        files = config["files"]
        files.pop("music_player")
        files.pop("pickle_file")
        return Config(**config)

    def to_toml(self) -> str:
        config = asdict(self)
        return toml.dumps(config)


@config_app.command
def edit():
    """Open config file in $EDITOR"""
    run([environ.get("EDITOR", "vim"), get_config_path()])


@config_app.command
def path():
    """Show config file path"""
    print(get_config_path())


def set_default_config(path: Path | None):
    if path is None:
        path = get_config_path()
    path.write_text(Config().to_toml())


global_group = Group("Global", sort_key=0)


SetKeyParameter = Annotated[
    set[str] | None,
    Parameter(negative=(), show_choices=False, show_default=False),
]


@dataclass
class SetFilesKeys:
    shared_directories: SetKeyParameter = None
    ignored_directories: SetKeyParameter = None


KeyParameter = Annotated[bool, Parameter(negative=(), show_default=False)]


@dataclass
class SetImportKeys:
    allow_prompt: KeyParameter = False
    disallow_prompt: KeyParameter = False
    ask_before_artist_update: KeyParameter = False
    update_aritst: KeyParameter = False
    update_disc: KeyParameter = False
    reformat: KeyParameter = False
    no_reformat: KeyParameter = False


StrKeyParameter = Annotated[
    str | Literal[False], Parameter(show_choices=False, show_default=False)
]


@dataclass
class SetNotificationsKeys:
    email_on: KeyParameter = False
    email_off: KeyParameter = False
    system_on: KeyParameter = False
    system_off: KeyParameter = False
    username: StrKeyParameter = False
    password: StrKeyParameter = False


@dataclass
class SetReformatKeys:
    expand_abbreviations: KeyParameter = False
    keep_abbreviations: KeyParameter = False
    remove_bracketed_instruments: KeyParameter = False
    keep_bracketed_instruments: KeyParameter = False
    remove_bracketed_years: KeyParameter = False
    keep_bracketed_years: KeyParameter = False


@config_app.command(name="set")
def set_config_value(
    *,
    files: Annotated[SetFilesKeys | None, Parameter(group="Files")] = None,
    import_config: Annotated[
        SetImportKeys | None,
        Parameter(name="import", group="Import", show_default=False),
    ] = None,
    notifications: Annotated[
        SetNotificationsKeys | None, Parameter(group="Notifications")
    ] = None,
    reformat: Annotated[
        SetReformatKeys | None, Parameter(group="Reformat", show_default=False)
    ] = None,
    restore_defaults: Annotated[bool, Parameter(group=global_group)] = False,
    clear_existing: Annotated[bool, Parameter(group="Files")] = False,
):
    """Set config values"""
    if restore_defaults:
        # TODO confirm this
        set_default_config(get_config_path())
        return
    print(files)
    print(import_config)
    print(notifications)
    print(reformat)


# TODO is it possible to generate these classes dynamically? Is that a good idea??
@dataclass
class ShowFilesKeys:
    shared_directories: KeyParameter = False
    ignored_directories: KeyParameter = False


@dataclass
class ShowImportKeys:
    allow_prompt: KeyParameter = False
    ask_before_artist_update: KeyParameter = False
    ask_before_disc_update: KeyParameter = False
    reformat: KeyParameter = False


@dataclass
class ShowNotificationsKeys:
    email_on: KeyParameter = False
    system_on: KeyParameter = False
    username: KeyParameter = False
    password: KeyParameter = False


@dataclass
class ShowReformatKeys:
    expand_abbreviations: KeyParameter = False
    remove_bracketed_instruments: KeyParameter = False
    remove_bracketed_years: KeyParameter = False


def get_value(
    keys: ShowFilesKeys
    | ShowImportKeys
    | ShowNotificationsKeys
    | ShowReformatKeys,
    values: Files | Import | Notifications | Reformat,
) -> str | set[str]:
    key = next(key for key, value in asdict(keys).items() if value)
    return cast(dict, values)[key]


@config_app.command
def show(
    *,
    files: Annotated[ShowFilesKeys | None, Parameter(group="Files")] = None,
    import_config: Annotated[
        ShowImportKeys | None, Parameter(name="import", group="Import")
    ] = None,
    notifications: Annotated[
        ShowNotificationsKeys | None, Parameter(group="Notifications")
    ] = None,
    reformat: Annotated[
        ShowReformatKeys | None, Parameter(group="Reformat")
    ] = None,
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
        config = Config()
    else:
        config = Config.from_toml()
    if not any((files, import_config, notifications, reformat)):
        config = config.to_toml()
        if not show_secrets:
            # TODO use capture groups
            config = re.sub('password = ".+"', 'password = "********"', config)
        print(Syntax(config, "toml", theme="ansi_dark"))
        return
    value = None
    if files:
        value = get_value(files, config.files)
    elif import_config:
        value = get_value(import_config, config.import_config)
    elif notifications:
        # TODO confirm showing of secrets here if key == password
        value = get_value(notifications, config.notifications)
    elif reformat:
        value = get_value(reformat, config.reformat)
    print(value)
