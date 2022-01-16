import pickle
from os import system, walk
from pathlib import Path
from re import search
from subprocess import run

from tinytag import TinyTag
from typer import confirm, echo

from .config import IGNORED_DIRECTORIES, MUSIC_PLAYER, PICKLE_FILE, SHARED_DIRECTORY
from .helpers import BRACKET_YEAR_REGEX, color

AUDIO_FILE_TYPES = ("*.mp3", "*.m4a", "*.flac", "*.aif*")
ERRORS = {
    "escape_error": "Error parsing path name",
    "conflicting_track_totals": "Album tracks include more than one track total number",
    "missing_track_total": "Album does not contain a track total number",
    "missing_tracks": "Album is missing tracks",
    "no_tracks": "Folder does not contain supported audio files",
    "wav_files": "Album is in wav format",
}
IMPORTABLE_ERROR_KEYS = [
    "conflicting_track_totals",
    "missing_track_total",
    "missing_tracks",
    "wav_files",
]


def get_imported_albums():
    with open(PICKLE_FILE, "rb") as raw_pickle:
        unpickled = pickle.load(raw_pickle)["taghistory"]
        albums = {album[0].decode() for album in unpickled}
    return albums


def get_album_directories():
    return [root for root, dirs, files in walk(SHARED_DIRECTORY) if files and not dirs]


def get_tracks(album):
    audio_files = list()
    for file_type in AUDIO_FILE_TYPES:
        audio_files.extend(Path(album).glob(file_type))
    return audio_files


def get_wav_tracks(album):
    return bool([track for track in Path(album).glob("*.wav")])


def get_track_total(tracks):
    message = None
    track_totals = {TinyTag.get(track).track_total for track in tracks}
    track_total = next(iter(track_totals), None)
    if len(track_totals) > 1:
        message = "conflicting_track_totals"
    elif not track_total:
        message = "missing_track_total"
    else:
        track_total = int(track_total)
    return track_total, message


def is_ignored_directory(album):
    for directory in IGNORED_DIRECTORIES:
        if directory in album:
            return True
    return False


def is_already_imported(album):
    return album in get_imported_albums()


def get_import_error_message(album, error_key):
    return f"{ERRORS[error_key]}: {color(album, 'cyan')}"


def get_single_or_double_quote(album):
    if "'" in album and '"' in album:
        return None
    elif '"' in album:
        return "'"
    else:
        return '"'


def beet_import(album):
    quote_character = get_single_or_double_quote(album)
    album = album.replace("$", r"\$")
    if quote_character:
        system(f"beet import {quote_character}{album}{quote_character}")
        return True
    else:
        return False


def import_wav_files(album):
    system(f"open -a '{MUSIC_PLAYER}' '{album}'")


def check_year(tracks):
    album = ""
    album_artist = ""
    fixable_year = False
    years = {TinyTag.get(track).year for track in tracks}
    year = next(iter(years), None)
    if len(years) == 1:
        album = next(iter({TinyTag.get(track).album for track in tracks}), "")
        found = search(BRACKET_YEAR_REGEX, album)
        if found:
            bracket_year = "".join(
                [character for character in found.group() if character.isnumeric()]
            )
            if bracket_year and confirm(
                f"Use bracket year ({bracket_year}) instead of year ({year}) for album:"
                f" {album}?"
            ):
                year = bracket_year
                album_artist = next(
                    iter({TinyTag.get(track).albumartist for track in tracks}), ""
                )
    return year, album, album_artist, fixable_year


def update_year(album_title, album_artist, new_year):
    run(
        [
            "beet",
            "modify",
            "-y",
            "-a",
            f"albumartist::^{album_artist}$",
            f"album::^{album_title}$",
            f"year={new_year}",
        ]
    )


def import_album(album, tracks, import_all, as_is):
    track_count = len(tracks)
    track_total, track_message = get_track_total(tracks)
    if import_all or track_count == track_total:
        error = None if beet_import(album) else "escape_error"
        if not as_is:
            year, album_title, album_artist, fixable_year = check_year(tracks)
            if not error and fixable_year and year and album_title:
                update_year(album_title, album_artist, year)
    elif track_message:
        error = track_message
    elif isinstance(track_total, int) and track_count > track_total:
        error = "conflicting_track_totals"
    else:
        error = "missing_tracks"
    return error


def import_albums(albums, as_is, import_all=False):
    errors = {key: list() for key in ERRORS.keys()}
    imports = False
    wav_imports = 0
    skipped_count = 0
    importable_error_albums = list()
    for album in albums:
        if not import_all:
            if is_ignored_directory(album):
                continue
            if is_already_imported(album):
                skipped_count += 1
                continue
        tracks = get_tracks(album)
        wav_tracks = get_wav_tracks(album)
        if tracks:
            error = import_album(album, tracks, import_all, as_is)
            if error:
                errors[error].append(get_import_error_message(album, error))
                if error in IMPORTABLE_ERROR_KEYS:
                    importable_error_albums.append(album)
            else:
                imports = True
        if wav_tracks:
            if import_all:
                import_wav_files(album)
                wav_imports += 1
            else:
                errors["wav_files"].append(get_import_error_message(album, "wav_files"))
                importable_error_albums.append(album)
        if not tracks and not wav_tracks:
            errors["no_tracks"].append(get_import_error_message(album, "no_tracks"))
    if wav_imports:
        echo(f"Imported {wav_imports} albums in WAV format.")
    if not import_all:
        echo(f"{skipped_count} albums skipped.")
    for key, error_list in errors.items():
        if error_list:
            color(key.replace("_", " ").upper(), echo=True)
            for error in error_list:
                echo(f"\t{error}")
    return imports, errors, importable_error_albums
