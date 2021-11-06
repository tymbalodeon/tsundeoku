import pickle
from glob import glob
from os import system, walk

from tinytag import TinyTag
from typer import colors, echo, secho, style

from .config import get_config_option, get_config_options

AUDIO_FILE_TYPES = (".mp3", ".m4a", ".flac")
COLORS = {
    "blue": colors.BLUE,
    "cyan": colors.CYAN,
    "green": colors.GREEN,
    "magenta": colors.MAGENTA,
    "red": colors.RED,
    "yellow": colors.YELLOW,
    "white": colors.WHITE,
}


def color(text, color="yellow", echo=False):
    if isinstance(text, int):
        text = f"{text:,}"
    return secho(text, fg=COLORS[color]) if echo else style(text, fg=COLORS[color])


def print_config_values():
    for option, value in get_config_options():
        echo(f"{color(option.replace('_', ' ').upper())}: {value}")


def get_imported_albums():
    with open(get_config_option("pickle_file"), "rb") as raw_pickle:
        unpickled = pickle.load(raw_pickle)["taghistory"]
        albums = {album[0].decode() for album in unpickled}
    return albums


def get_album_directories():
    return [
        root
        for root, dirs, files in walk(get_config_option("shared_directory"))
        if files and not dirs
    ]


def get_audio_files():
    audio_files = list()
    for file_type in AUDIO_FILE_TYPES:
        audio_files.extend(glob(file_type))
    return audio_files


def get_track_total(tracks):
    track_total = 0
    message = None
    track_totals = {TinyTag.get(track).track_total for track in tracks}
    if not track_totals:
        message = "missing"
    elif len(track_totals) > 1:
        message = "conflicting"
    else:
        track_total = int(next(iter(track_totals)))
    return track_total, message


def get_single_or_double_quote(album):
    if "'" in album and '"' in album:
        return None
    elif '"' in album:
        return "'"
    else:
        return '"'


def is_already_imported(album):
    return album in get_imported_albums()


def import_or_get_errors(album):
    skipped = False
    imported = False
    error = None
    if is_already_imported(album):
        skipped = True
        return skipped, imported, error
    tracks = get_audio_files()
    track_count = len(tracks)
    track_total, message = get_track_total(tracks)
    quote_character = get_single_or_double_quote(album)
    if not tracks:
        error = (
            "Folder is empty or audio is in wav format (please wait for sync or"
            f" resolve manually): '{album}'"
        )
    elif message == "conflicting":
        error = (
            f'Possible multi-disc album detected (please resolve manually): "{album}"'
        )
    elif message == "missing":
        error = (
            "Album does not contain a track total number"
            f' (please resolve manually): "{album}"'
        )
    elif track_count == track_total:
        if quote_character:
            system(f"beet import {quote_character}{album}{quote_character}")
            imported = True
        else:
            error = f'Annoyingly named directory (please resolve manually): "{album}"'
    elif track_count > track_total:
        error = (
            f'Possible multi-disc album detected (please resolve manually): "{album}"'
        )
    else:
        error = (
            "Missing tracks (please wait for sync or resolve"
            f' manually): "{album}"\n\tTrack total: {track_total}'
        )
    return skipped, imported, error


def import_complete_albums():
    errors = list()
    skipped_count = 0
    imports = False
    bulk_fix_albums = list()
    skip_directories = get_config_option("skip_directories")
    for album in get_album_directories():
        if skip_directories in album:
            continue
        else:
            skipped, imported, error = import_or_get_errors(album)
            if imported:
                imports = True
            if skipped:
                skipped_count += 1
            if error:
                errors.append(error)
                bulk_fix_albums.append(album)
    print(f"{skipped_count} albums skipped.")
    for error in errors:
        color(error, echo=True)
    return imports, errors, bulk_fix_albums


def import_error_albums(albums):
    for album in albums:
        quote_character = get_single_or_double_quote(album)
        system(f"beet import {quote_character}{album}{quote_character}")
