import pickle
from os import system, walk
from pathlib import Path

from tinytag import TinyTag
from typer import echo

from .config import get_config_option
from .helpers import color

AUDIO_FILE_TYPES = ("*.mp3", "*.m4a", "*.flac")
ERRORS = {
    "escape_error": f"Annoyingly named directory (please resolve manually)",
    "conflicting_track_totals": (
        f"Possible multi-disc album detected (please resolve manually)"
    ),
    "missing_track_total": (
        f"Album does not contain a track total number (please resolve manually)"
    ),
    "missing_tracks": f"Annoyingly named directory (please resolve manually)",
    "no_tracks": (
        f"Folder is empty or audio is in wav format (please wait for sync or"
        f" resolve manually)"
    ),
}
IMPORTABLE_ERROR_KEYS = [
    "conflicting_track_totals",
    "missing_track_total",
    "missing_tracks",
]


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


def get_tracks(album):
    audio_files = list()
    for file_type in AUDIO_FILE_TYPES:
        audio_files.extend(Path(album).glob(file_type))
    return audio_files


def get_track_total(tracks):
    track_total = 0
    message = None
    track_totals = {TinyTag.get(track).track_total for track in tracks}
    track_total = next(iter(track_totals))
    if len(track_totals) > 1:
        message = "conflicting_track_totals"
    elif not track_total:
        message = "missing_track_total"
    else:
        track_total = int(track_total)
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


def get_import_error_message(album, error_key):
    return f"{ERRORS[error_key]}: {album}"


def beet_import(album):
    quote_character = get_single_or_double_quote(album)
    if quote_character:
        system(f"beet import {quote_character}{album}{quote_character}")
        return True
    else:
        return False


def import_album(album, tracks):
    imported = False
    error_key = None
    track_count = len(tracks)
    track_total, message = get_track_total(tracks)
    if track_count == track_total:
        error = beet_import(album)
        if error:
            error_key = "escape_error"
    elif message:
        error_key = message
    elif isinstance(track_total, int) and track_count > track_total:
        error_key = "conflicting_track_totals"
    else:
        error_key = "missing_tracks"
    return imported, error_key


def import_albums(albums, import_all=False):
    errors = list()
    imports = False
    skipped_count = 0
    importable_error_albums = list()
    for album in albums:
        if not import_all:
            if get_config_option("skip_directories") in album:
                continue
            if is_already_imported(album):
                skipped_count += 1
                continue
        tracks = get_tracks(album)
        if not tracks:
            errors.append(get_import_error_message(album, "no_tracks"))
            continue
        imported, error_key = import_album(album, tracks)
        if imported:
            imports = True
        if error_key:
            errors.append(get_import_error_message(album, error_key))
            if error_key in IMPORTABLE_ERROR_KEYS:
                importable_error_albums.append(album)
    if not import_all:
        echo(f"{skipped_count} albums skipped.")
    for error in errors:
        color(error, echo=True)
    return imports, errors, importable_error_albums
