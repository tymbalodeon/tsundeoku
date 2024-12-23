import re
from dataclasses import asdict, dataclass, field
from os import environ, getcwd
from pathlib import Path
from subprocess import run
from typing import Annotated, Generator, Literal, Sequence, cast

import toml
from cyclopts import App, Group, Parameter, Token
from cyclopts.validators import Path as PathValidator
from pydantic import BaseModel, Field
from rich import print
from rich.prompt import Confirm
from rich.syntax import Syntax

config_app = App(
    name="config", help="Show and set config values.", version_flags=()
)

Paths = Annotated[set[str], Parameter(negative=(), show_default=False)]


class Files(BaseModel):
    shared_directories: Paths = field(
        default_factory=lambda: {str(Path.home() / "Dropbox")}
    )
    ignored_directories: Paths = field(default_factory=set)

    @staticmethod
    def paths_to_str(paths: set[Path]) -> set[str]:
        return {str(path) for path in paths}


Bool = Annotated[bool, Parameter(negative=())]


class Import(BaseModel):
    allow_prompt: Bool = False
    ask_before_artist_update: Bool = True
    ask_before_disc_update: Bool = True
    reformat: Bool = False


class Notifications(BaseModel):
    email_on: Bool = False
    system_on: Bool = False
    username: str | None = None
    password: str | None = None


class Reformat(BaseModel):
    expand_abbreviations: Bool = False
    remove_bracketed_instruments: Bool = False
    remove_bracketed_years: Bool = False


def get_app_name() -> Literal["tsundeoku"]:
    return "tsundeoku"


def get_config_path() -> Path:
    app_name = get_app_name()
    return Path.home() / f".config/{app_name}/{app_name}.toml"


class Config(BaseModel):
    files: Files = field(default_factory=lambda: Files())
    import_config: Import = Field(
        alias="import", default_factory=lambda: Import()
    )
    notifications: Notifications = field(
        default_factory=lambda: Notifications()
    )
    reformat: Reformat = field(default_factory=lambda: Reformat())

    @staticmethod
    def from_toml(config_path: Path | None = None) -> "Config":
        if config_path is None:
            config_path = get_config_path()
        config = toml.loads(config_path.read_text())
        files = config.pop("files")
        Files.model_validate(files)
        Config.model_validate(config)
        config = Config(**config, files=files)
        return config

    def to_toml(self) -> str:
        return toml.dumps(self.model_dump(by_alias=True))


def is_toml(_, config_path: Path) -> None:
    is_valid = True
    if config_path.exists():
        try:
            if not bool(toml.loads(config_path.read_text())):
                is_valid = False
        except Exception:
            is_valid = False
    if not is_valid:
        raise ValueError("Must be a TOML file")


ConfigPath = Annotated[Path, Parameter(validator=is_toml)]


@config_app.command
def edit(*, config_path: ConfigPath = get_config_path()) -> None:
    """Open config file in $EDITOR"""
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(Config().to_toml())
    run([environ.get("EDITOR", "vim"), config_path])


@config_app.command
def path() -> None:
    """Show config file path"""
    print(get_config_path())


def set_default_config(path: Path | None) -> None:
    if path is None:
        path = get_config_path()
    path.write_text(Config().to_toml())


global_group = Group("Global", sort_key=0)


SetPathsParameter = Annotated[
    set[str] | None,
    Parameter(negative=(), show_choices=False, show_default=False),
]


@dataclass
class SetFilesKeys:
    shared_directories: SetPathsParameter = None
    ignored_directories: SetPathsParameter = None


SetBoolParameter = Annotated[bool | None, Parameter(show_default=False)]


@dataclass
class SetImportKeys:
    allow_prompt: Annotated[
        SetBoolParameter, Parameter(negative="--import.disallow-prompt")
    ] = False
    ask_before_artist_update: Annotated[
        SetBoolParameter, Parameter(negative="--import.auto-update-artist")
    ] = False
    reformat: Annotated[
        SetBoolParameter, Parameter(negative="--import.auto-update-disc")
    ] = False


SetStrParameter = Annotated[
    str | Literal[False], Parameter(show_choices=False, show_default=False)
]


@dataclass
class SetNotificationsKeys:
    email_on: Annotated[
        SetBoolParameter, Parameter(negative="--notifications.email-off")
    ] = None
    system_on: Annotated[
        SetBoolParameter, Parameter(negative="--notifications.system-off")
    ] = None
    username: SetStrParameter = False
    password: SetStrParameter = False


@dataclass
class SetReformatKeys:
    expand_abbreviations: Annotated[
        SetBoolParameter, Parameter(negative="--reformat.keep-abbreviations")
    ] = False
    remove_bracketed_instruments: Annotated[
        SetBoolParameter,
        Parameter(negative="--reformat.keep-bracketed-instruments"),
    ] = False
    remove_bracketed_years: Annotated[
        SetBoolParameter, Parameter(negative="--reformat.bracketed-years")
    ] = False


@config_app.command(name="set")
def set_config_values(
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
    restore_default: Annotated[bool, Parameter(group=global_group)] = False,
    clear_existing: Annotated[bool, Parameter(group="Files")] = False,
    config_path: Annotated[
        ConfigPath, Parameter(group="Global")
    ] = get_config_path(),
) -> None:
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
    if restore_default:
        if Confirm.ask("Are you sure you want to reset your config?"):
            set_default_config(config_path)
        return
    print(files)
    print(import_config)
    print(notifications)
    print(reformat)


# TODO is it possible to generate these classes dynamically? Is that a good idea??
@dataclass
class ShowFilesKeys:
    all: SetBoolParameter = False
    shared_directories: SetBoolParameter = False
    ignored_directories: SetBoolParameter = False

    @property
    def key_name(self) -> str:
        return "files"


@dataclass
class ShowImportKeys:
    all: SetBoolParameter = False
    allow_prompt: SetBoolParameter = False
    ask_before_artist_update: SetBoolParameter = False
    ask_before_disc_update: SetBoolParameter = False
    reformat: SetBoolParameter = False

    @property
    def key_name(self) -> str:
        return "import"


@dataclass
class ShowNotificationsKeys:
    all: SetBoolParameter = False
    email_on: SetBoolParameter = False
    system_on: SetBoolParameter = False
    username: SetBoolParameter = False
    password: SetBoolParameter = False

    @property
    def key_name(self) -> str:
        return "notifications"


@dataclass
class ShowReformatKeys:
    all: SetBoolParameter = False
    expand_abbreviations: SetBoolParameter = False
    remove_bracketed_instruments: SetBoolParameter = False
    remove_bracketed_years: SetBoolParameter = False

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


def parse_path(_, tokens: Sequence[Token]) -> Path:
    value = tokens[0].value.lower()
    if Path(value).exists():
        return Path(value)
    else:
        return Path(getcwd()) / Path(value)


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
        Path,
        Parameter(
            group="Global",
            converter=parse_path,
            validator=(PathValidator(exists=True, dir_okay=False), is_toml),
        ),
    ] = get_config_path(),
) -> None:
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
            password = re.compile(r'password = "(?P<password>.+)"').search(
                config
            )
            if password is not None:
                config = config.replace(password.group("password"), "********")
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
        table_values = cast(
            BaseModel, getattr(config, table.key_name)
        ).model_dump()
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
