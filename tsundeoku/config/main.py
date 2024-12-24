import re
from dataclasses import asdict, dataclass, field
from os import environ
from pathlib import Path
from subprocess import run
from typing import Annotated, Generator, Literal

import toml
from cyclopts import App, Group, Parameter
from cyclopts.config import Toml
from rich import print
from rich.prompt import Confirm
from rich.syntax import Syntax

config_app = App(
    name="config", help="Show and set config values.", version_flags=()
)

PathSet = Annotated[set[Path], Parameter(negative=(), show_default=False)]


@dataclass
class Files:
    shared_directories: PathSet = field(
        default_factory=lambda: {Path.home() / "Dropbox"}
    )
    ignored_directories: PathSet = field(default_factory=set)

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


Bool = Annotated[bool, Parameter(negative=())]


@dataclass
class Import:
    allow_prompt: Bool = False
    ask_before_artist_update: Bool = True
    ask_before_disc_update: Bool = True
    reformat: Bool = False


@dataclass
class Notifications:
    email_on: Bool = False
    system_on: Bool = False
    username: str | None = None
    password: str | None = None


@dataclass
class Reformat:
    expand_abbreviations: Bool = False
    remove_bracketed_instruments: Bool = False
    remove_bracketed_years: Bool = False


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

    # TODO validate config file
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
        files = Files(**config["files"])
        import_config = Import(**config["import_config"])
        notifications = Notifications(**config["notifications"])
        reformat = Reformat(**config["reformat"])
        return Config(files, import_config, notifications, reformat)

    def to_toml(self) -> str:
        config = asdict(self)
        if isinstance(self.files, Files):
            config["files"] = self.files.to_dict()
        return toml.dumps(config)


@config_app.command
def edit(*, config_path: Path = get_config_path()):
    """Open config file in $EDITOR"""
    run([environ.get("EDITOR", "vim"), config_path])


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
    config_path: Annotated[
        Path, Parameter(group="Global")
    ] = get_config_path(),
):
    """Set config values

    Parameters
    ----------
    files
        ...DIRECTORIES
    notifications.username
        USERNAME
    notifications.password
        PASSWORD
    """
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
    all: KeyParameter = False
    shared_directories: KeyParameter = False
    ignored_directories: KeyParameter = False

    @property
    def key_name(self) -> str:
        return "files"


@dataclass
class ShowImportKeys:
    all: KeyParameter = False
    allow_prompt: KeyParameter = False
    ask_before_artist_update: KeyParameter = False
    ask_before_disc_update: KeyParameter = False
    reformat: KeyParameter = False

    @property
    def key_name(self) -> str:
        return "import"


@dataclass
class ShowNotificationsKeys:
    all: KeyParameter = False
    email_on: KeyParameter = False
    system_on: KeyParameter = False
    username: KeyParameter = False
    password: KeyParameter = False

    @property
    def key_name(self) -> str:
        return "notifications"


@dataclass
class ShowReformatKeys:
    all: KeyParameter = False
    expand_abbreviations: KeyParameter = False
    remove_bracketed_instruments: KeyParameter = False
    remove_bracketed_years: KeyParameter = False

    @property
    def key_name(self) -> str:
        return "reformat"


def get_values(
    dictionary: dict[str, str] | dict[str, set[str]],
) -> Generator[set[str] | str | None, None, None]:
    for value in dictionary.values():
        if isinstance(value, dict):
            yield from get_values(value)
        else:
            yield value


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
    config_path: Annotated[
        Path, Parameter(group="Global")
    ] = get_config_path(),
):
    """
    Show config values

    Parameters
    ----------
    default
        Show default value(s)
    show_secrets
        Show secret config values
    """
    if default:
        config = Config()
    else:
        config = Config.from_toml(config_path)
    if not any((files, import_config, notifications, reformat)):
        config = config.to_toml()
        if not show_secrets:
            # TODO use capture groups
            config = re.sub('password = ".+"', 'password = "********"', config)
        print(Syntax(config, "toml", theme="ansi_dark"))
        return
    tables = tuple(
        table
        for table in (files, import_config, notifications, reformat)
        if table is not None
    )
    values = {}
    for table in tables:
        requested_values = {
            key: value for key, value in asdict(table).items() if value
        }
        table_values = asdict(getattr(config, table.key_name))
        if "all" not in requested_values:
            for key in tuple(table_values.keys()):
                if key not in requested_values:
                    table_values.pop(key)
        values[table.key_name] = table_values
    if len(values.keys()) == 1:
        value = next(get_values(values))
        if (
            "notifications" in values.keys()
            and "password" in values["notifications"].keys()
        ) and not show_secrets:
            show_password = Confirm.ask(
                "Are you sure you want to show the password?"
            )
            if not show_password:
                return
        if isinstance(value, set):
            value = list(Files.paths_to_str(set(Path(path) for path in value)))
        print(value)
    else:
        print(Syntax(toml.dumps(values), "toml", theme="ansi_dark"))
