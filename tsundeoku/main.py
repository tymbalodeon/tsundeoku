from glob import glob
from pathlib import Path
from typing import Annotated

from cyclopts import App, Group, Parameter
from cyclopts.config import Toml
from cyclopts.validators import Path as PathValidator

from tsundeoku.config import (
    Config,
    config_app,
    get_app_name,
    get_config_path,
    is_toml,
    parse_path,
)
from tsundeoku.import_command import import_file
from tsundeoku.schedule import schedule_app, send_email

app = App(
    config=Toml(get_config_path(), allow_unknown=True),
    help="""
積んでおく (tsundeoku) –– "to pile up for later"

Import audio files from a shared folder to a local library""",
)
app.command(config_app)
app.command(schedule_app)


global_group = Group("Global", sort_key=0)


@app.command(name="import")
def import_command(
    *,
    shared_directories: Annotated[
        tuple[str, ...], Parameter(negative=())
    ] = Config().items.import_config.shared_directories,
    ignored_paths: Annotated[
        tuple[str, ...], Parameter(negative=())
    ] = Config().items.import_config.ignored_paths,
    local_directory: Annotated[
        str, Parameter(negative=())
    ] = Config().items.import_config.local_directory,
    reformat: bool = Config().items.import_config.reformat,
    ask_before_artist_update: Annotated[
        bool, Parameter(negative="--auto-update-artist")
    ] = Config().items.import_config.ask_before_artist_update,
    ask_before_disc_update: Annotated[
        bool,
        Parameter(negative="--auto-update-disc"),
    ] = Config().items.import_config.ask_before_disc_update,
    config_path: Annotated[
        Path,
        Parameter(
            converter=parse_path,
            group=global_group,
            validator=(PathValidator(exists=True, dir_okay=False), is_toml),
        ),
    ] = get_config_path(),
    force: Annotated[bool, Parameter(group=global_group, negative=())] = False,
    allow_prompt: Annotated[bool, Parameter(show=False)] = True,
) -> None:
    """Copy new adds from your shared folder to your local library.

    Parameters
    ----------
    shared_directories
        Directories to scan for new audio files.
    ignored_paths
        Paths to skip when scanning for new audio files.
    local_directory
        Directory to copy new audio files into.
    reformat
        Toggle reformatting.
    ask_before_disc_update
        Toggle confirming disc updates.
    ask_before_artist_update
        Toggle confirming removal of brackets from artist field.
    """
    if config_path != get_config_path():
        config = Config.from_toml(config_path)
        shared_directories = config.items.import_config.shared_directories
        ignored_paths = config.items.import_config.ignored_paths
        local_directory = config.items.import_config.local_directory
        reformat = config.items.import_config.reformat
        ask_before_artist_update = (
            config.items.import_config.ask_before_artist_update
        )
        ask_before_disc_update = (
            config.items.import_config.ask_before_disc_update
        )
    files_requiring_prompt = []
    for directory in shared_directories:
        shared_directory_files = tuple(
            file for file in sorted(glob(f"{directory}/**/*", recursive=True))
        )
        imported_files_file = (
            Path.home() / f".local/share/{get_app_name()}/imported_files"
        )
        if imported_files_file.exists():
            imported_files = imported_files_file.read_text().splitlines()
        else:
            imported_files_file.parent.mkdir(parents=True, exist_ok=True)
            imported_files_file.touch()
            imported_files = []
        for file in imported_files:
            if file not in shared_directory_files:
                imported_files.remove(file)
            imported_files_file.write_text(f"{'\n'.join(imported_files)}\n")
        for file in shared_directory_files:
            if (
                import_file(
                    file=file,
                    imported_files_file=imported_files_file,
                    imported_files=imported_files,
                    local_directory=local_directory,
                    ignored_paths=ignored_paths,
                    reformat=reformat,
                    ask_before_artist_update=ask_before_artist_update,
                    ask_before_disc_update=ask_before_disc_update,
                    allow_prompt=False,
                    force=force,
                )
                is False
            ):
                files_requiring_prompt.append(file)
        if allow_prompt:
            for file in shared_directory_files:
                import_file(
                    file=file,
                    imported_files_file=imported_files_file,
                    imported_files=imported_files,
                    local_directory=local_directory,
                    ignored_paths=ignored_paths,
                    reformat=reformat,
                    ask_before_artist_update=ask_before_artist_update,
                    ask_before_disc_update=ask_before_disc_update,
                    allow_prompt=True,
                    force=force,
                )
        else:
            send_email(get_app_name(), "\n".join(files_requiring_prompt))
