import re
from dataclasses import asdict, dataclass, field
from os import environ, getcwd
from pathlib import Path
from subprocess import run
from typing import Annotated, Any, Generator, Literal, Sequence, cast

import toml
from cyclopts import App, Group, Parameter, Token
from cyclopts.validators import Path as PathValidator
from pydantic import AliasChoices, BaseModel, Field
from rich import print
from rich.prompt import Confirm
from rich.syntax import Syntax

config_app = App(
    name="config", help="Show and set config values.", version_flags=()
)

Paths = Annotated[tuple[str, ...], Parameter(negative=(), show_default=False)]
Bool = Annotated[bool, Parameter(negative=())]


class Import(BaseModel):
    shared_directories: Paths = Field(
        default_factory=lambda: (str(Path.home() / "Dropbox"),)
    )
    ignored_paths: Paths = ()
    local_directory: str = str(Path.home() / "Music")
    reformat: Bool = False
    ask_before_artist_update: Bool = True
    ask_before_disc_update: Bool = True
    expand_abbreviations: Bool = False
    remove_bracketed_instruments: Bool = False
    remove_bracketed_years: Bool = False


class Schedule(BaseModel):
    email_on: Bool = False
    system_on: Bool = False
    username: str | None = None
    password: str | None = None


def get_app_name() -> Literal["tsundeoku"]:
    return "tsundeoku"


def get_config_path() -> Path:
    app_name = get_app_name()
    return Path.home() / f".config/{app_name}/{app_name}.toml"


class ConfigItems(BaseModel):
    import_config: Import = Field(
        alias="import",
        validation_alias=AliasChoices("import", "import_config"),
        default_factory=lambda: Import(),
    )
    schedule: Schedule = Field(default_factory=lambda: Schedule())


@dataclass
class Config:
    items: ConfigItems = field(default_factory=lambda: ConfigItems())
    path: Path = get_config_path()

    @property
    def shared_directories(self):
        pass

    @staticmethod
    def from_dict(
        config: dict[str, Any], path: Path | None = None
    ) -> "Config":
        if path is None:
            path = get_config_path()
        ConfigItems.model_validate(config)
        return Config(items=ConfigItems(**config), path=path)

    @staticmethod
    def from_toml(path: Path | None = None) -> "Config":
        if path is None:
            path = get_config_path()
        config = toml.loads(path.read_text())
        return Config.from_dict(config, path=path)

    def to_toml(self) -> str:
        return toml.dumps(self.items.model_dump(by_alias=True))

    def save(self, path: Path | None = None) -> None:
        if path is None:
            path = self.path
        path.write_text(self.to_toml())


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


def display_config_toml(config: str) -> None:
    print(Syntax(config, "toml", theme="ansi_dark"))


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
    tuple[str, ...] | None,
    Parameter(negative=(), show_choices=False, show_default=False),
]


@dataclass
class HasImportName:
    @property
    def key_name(self) -> Literal["import_config"]:
        return "import_config"


@dataclass
class HasScheduleName:
    @property
    def key_name(self) -> Literal["schedule"]:
        return "schedule"


SetBoolParameter = Annotated[bool | None, Parameter(show_default=False)]


@dataclass
class SetImportKeys(HasImportName):
    shared_directories: SetPathsParameter = None
    ignored_paths: SetPathsParameter = None
    local_directory: Annotated[
        str | None, Parameter(negative=(), show_default=False)
    ] = None
    reformat: Annotated[
        SetBoolParameter, Parameter(negative="--import.no-reformat")
    ] = None
    ask_before_artist_update: Annotated[
        SetBoolParameter, Parameter(negative="--import.auto-update-artist")
    ] = None
    ask_before_disc_update: Annotated[
        SetBoolParameter, Parameter(negative="--import.auto-update-disc")
    ] = None
    expand_abbreviations: Annotated[
        SetBoolParameter, Parameter(negative="--reformat.keep-abbreviations")
    ] = None
    remove_bracketed_instruments: Annotated[
        SetBoolParameter,
        Parameter(negative="--reformat.keep-bracketed-instruments"),
    ] = None
    remove_bracketed_years: Annotated[
        SetBoolParameter, Parameter(negative="--reformat.bracketed-years")
    ] = None


SetStrParameter = Annotated[
    str | Literal[False], Parameter(show_choices=False, show_default=False)
]


@dataclass
class SetScheduleKeys(HasScheduleName):
    email_on: Annotated[
        SetBoolParameter, Parameter(negative="--schedule.email-off")
    ] = None
    system_on: Annotated[
        SetBoolParameter, Parameter(negative="--schedule.system-off")
    ] = None
    username: SetStrParameter = False
    password: SetStrParameter = False


def merge_dicts(
    a: dict[str, Any], b: dict[str, Any], clear_existing_sets=False
) -> dict[str, Any]:
    merged = a.copy()
    for key, value in b.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = merge_dicts(
                merged[key], value, clear_existing_sets=clear_existing_sets
            )
        elif (
            key in merged
            and isinstance(merged[key], set)
            and not clear_existing_sets
        ):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def get_requested_tables(
    tables: tuple[HasImportName | HasScheduleName | None, ...],
) -> tuple[HasImportName | HasScheduleName, ...]:
    return tuple(table for table in tables if table is not None)


def get_requested_items(table_items: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in table_items.items() if value is not None
    }


@config_app.command(name="set")
def set_config_values(
    *,
    import_config: Annotated[
        SetImportKeys | None,
        Parameter(name="import", group="Import", show_default=False),
    ] = None,
    schedule: Annotated[
        SetScheduleKeys | None, Parameter(group="Schedule")
    ] = None,
    restore_defaults: Annotated[bool, Parameter(group=global_group)] = False,
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
    schedule.username
        USERNAME
    schedule.password
        PASSWORD
    """
    if restore_defaults:
        if Confirm.ask(
            "Are you sure you want to reset your config to the default?"
        ):
            Config(path=config_path).save()
        return
    config_items = Config.from_toml(config_path).items.model_dump()
    requested_tables = get_requested_tables((import_config, schedule))
    items = {key: {} for key in {table.key_name for table in requested_tables}}
    for table in requested_tables:
        table_items = asdict(table)
        if table.key_name == "schedule":
            for key, value in table_items.items():
                if key in ("username", "password") and value is False:
                    table_items[key] = None
        requested_values = get_requested_items(table_items)
        for key, value in requested_values.items():
            items[table.key_name][key] = value
    config_items = merge_dicts(
        config_items, items, clear_existing_sets=clear_existing
    )
    config = Config.from_dict(config_items, path=config_path)
    config.save()


@dataclass
class ShowImportKeys(HasImportName):
    all: SetBoolParameter = None
    shared_directories: SetBoolParameter = None
    ignored_paths: SetBoolParameter = None
    local_directory: SetBoolParameter = None
    reformat: SetBoolParameter = None
    ask_before_artist_update: SetBoolParameter = None
    ask_before_disc_update: SetBoolParameter = None
    expand_abbreviations: SetBoolParameter = None
    remove_bracketed_instruments: SetBoolParameter = None
    remove_bracketed_years: SetBoolParameter = None


@dataclass
class ShowScheduleKeys(HasScheduleName):
    all: SetBoolParameter = None
    email_on: SetBoolParameter = None
    system_on: SetBoolParameter = None
    username: SetBoolParameter = None
    password: SetBoolParameter = None


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
    import_config: Annotated[
        ShowImportKeys | None, Parameter(name="import", group="Import")
    ] = None,
    notifications: Annotated[
        ShowScheduleKeys | None, Parameter(group="Notifications")
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
    if not any((import_config, notifications)):
        config = config.to_toml()
        if not show_secrets:
            password = re.compile(r'password = "(?P<password>.+)"').search(
                config
            )
            if password is not None:
                config = config.replace(password.group("password"), "********")
        display_config_toml(config)
        return
    requested_tables = get_requested_tables((import_config, notifications))
    items = {}
    for table in requested_tables:
        requested_values = get_requested_items(asdict(table))
        table_values = cast(
            BaseModel, getattr(config.items, table.key_name)
        ).model_dump()
        if "all" not in requested_values:
            for key in tuple(table_values.keys()):
                if key not in requested_values:
                    table_values.pop(key)
        items[table.key_name] = table_values
    if any(
        (
            value
            for value in items.values()
            if isinstance(value, dict) and len(value.keys()) == 1
        )
    ):
        value = next(get_values(items))
        if (
            "notifications" in items.keys()
            and "password" in items["notifications"].keys()
        ) and not show_secrets:
            show_password = Confirm.ask(
                "Are you sure you want to show the password?"
            )
            if not show_password:
                return
        if isinstance(value, set):
            value = list(value)
        print(value)
    else:
        items["import"] = items.pop("import_config")
        display_config_toml(toml.dumps(items))
