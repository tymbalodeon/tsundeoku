import pickle
from glob import glob
from os import system, walk

from tinytag import TinyTag

from .config import get_config_option
from .helpers import color

AUDIO_FILE_TYPES = (".mp3", ".m4a", ".flac")
ERRORS = {
    "no_tracks": (
        f"Folder is empty or audio is in wav format (please wait for sync or"
        f" resolve manually)"
    ),
    "conflicting_track_totals": (
        f"Possible multi-disc album detected (please resolve manually)"
    ),
    "missing_track_total": (
        f"Album does not contain a track total number (please resolve manually)"
    ),
    "escape_error": f"Annoyingly named directory (please resolve manually)",
    "missing_tracks": f"Annoyingly named directory (please resolve manually)",
}


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
        message = "missing_track_total"
    elif len(track_totals) > 1:
        message = "conflicting_track_totals"
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


def get_import_error_message(album, error_key):
    return f"{ERRORS[error_key]}: {album}"


def import_or_get_errors(album, tracks, import_all=False):
    imported = False
    error_key = None
    track_count = len(tracks)
    track_total, message = get_track_total(tracks)
    if import_all or track_count == track_total:
        quote_character = get_single_or_double_quote(album)
        if quote_character:
            system(f"beet import {quote_character}{album}{quote_character}")
            imported = True
        else:
            error_key = "escape_error"
    elif message:
        error_key = message
    elif track_count > track_total:
        error_key = "conflicting_track_totals"
    else:
        error_key = "missing_tracks"
    return imported, get_import_error_message(album, error_key)


def import_complete_albums():
    errors = list()
    skipped_count = 0
    imports = False
    bulk_fix_albums = list()
    for album in get_album_directories():
        if is_already_imported(album):
            skipped_count += 1
            continue
        tracks = get_audio_files()
        if not tracks:
            errors.append(get_import_error_message(album, "no_tracks"))
            continue
        imported, error = import_or_get_errors(album, tracks)
        if imported:
            imports = True
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
