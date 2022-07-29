import pickle
from os import system, walk
from pathlib import Path
from re import escape, search, sub
from typing import Optional

from beets.importer import history_add
from tinytag import TinyTag
from typer import confirm, echo

from .config import IGNORED_DIRECTORIES, MUSIC_PLAYER, PICKLE_FILE, SHARED_DIRECTORY
from .helpers import BRACKET_DISC_REGEX, BRACKET_YEAR_REGEX, Color, color, modify_tracks

AUDIO_FILE_TYPES = ("*.mp3", "*.Mp3", "*.m4a", "*.flac", "*.aif*")
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


def get_imported_albums() -> set[str]:
    with open(PICKLE_FILE, "rb") as raw_pickle:
        unpickled = pickle.load(raw_pickle)["taghistory"]
        return {album[0].decode() for album in unpickled}


IMPORTED_ALBUMS = get_imported_albums()


def get_album_directories() -> list[str]:
    return [root for root, dirs, files in walk(SHARED_DIRECTORY) if files and not dirs]


def get_tracks(album: str) -> list[Path]:
    audio_files: list[Path] = list()
    for file_type in AUDIO_FILE_TYPES:
        audio_files.extend(Path(album).glob(file_type))
    return audio_files


def get_wav_tracks(album: str) -> bool:
    return bool([track for track in Path(album).glob("*.wav")])


def get_track_total(tracks: list[Path]) -> tuple[Optional[int], Optional[str]]:
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


def is_ignored_directory(album: str) -> bool:
    for directory in IGNORED_DIRECTORIES:
        if directory in album:
            return True
    return False


def is_already_imported(album: str) -> bool:
    return album in IMPORTED_ALBUMS


def get_single_or_double_quote(album: str) -> str:
    if "'" in album and '"' in album:
        return ""
    elif '"' in album:
        return "'"
    else:
        return '"'


def beet_import(album: str) -> bool:
    quote_character = get_single_or_double_quote(album)
    if not quote_character:
        album = album.replace('"', r"\"")
        quote_character = '"'
    album = album.replace("$", r"\$")
    if quote_character:
        system(f"beet import {quote_character}{album}{quote_character}")
        return True
    else:
        return False


def import_wav_files(album: str):
    system(f"open -a '{MUSIC_PLAYER}' '{album}'")


def get_album_title(tracks: list[Path]) -> str:
    return next(iter({TinyTag.get(track).album for track in tracks}), "")


def get_artist_and_field(tracks: list[Path]) -> tuple[str, str]:
    field = "albumartist"
    artist = ""
    try:
        artist = next(iter({TinyTag.get(track).albumartist for track in tracks}))
    except Exception:
        artists = {TinyTag.get(track).artist for track in tracks}
        if len(artists) > 1:
            field = ""
        else:
            artist = next(iter(artists), "")
            field = "artist"
    return artist, field


def style_album(album: str) -> str:
    return color(album, Color.BLUE, bold=True)


def should_update(
    field: str, bracket_value: str, existing_value: str, album: str
) -> bool:
    return confirm(
        f"Use bracket {field} [{color(bracket_value, bold=True)}] instead of"
        f" {field} ({color(existing_value, bold=True)}) for album:"
        f" {style_album(album)}?"
    )


def check_year(tracks: list[Path], album: Optional[str]) -> tuple[Optional[str], bool]:
    fixable_year = False
    years = {TinyTag.get(track).year for track in tracks}
    year = next(iter(years), "")
    if len(years) == 1:
        album = str(next(iter({TinyTag.get(track).album for track in tracks}), ""))
        found = search(BRACKET_YEAR_REGEX, album)
        bracket_year = (
            "".join([character for character in found.group() if character.isnumeric()])
            if found
            else ""
        )
        if (
            bracket_year
            and bracket_year != year
            and should_update("year", bracket_year, year, album)
        ):
            year = bracket_year
            fixable_year = True
    return year, fixable_year


def check_disc(
    tracks: list[Path], album: str, skip_confirm_disc_overwrite: bool
) -> tuple[Optional[str], Optional[str], bool, bool]:
    fixable_disc = False
    remove_bracket_disc = False
    discs = {TinyTag.get(track).disc for track in tracks}
    disc = next(iter(discs), "")
    disc_total = ""
    found = search(BRACKET_DISC_REGEX, album)
    bracket_disc = (
        "".join([character for character in found.group() if character.isnumeric()])
        if found
        else ""
    )
    if (
        bracket_disc
        and bracket_disc != disc
        and should_update("disc", bracket_disc, disc, album)
    ):
        disc = bracket_disc
        fixable_disc = True
    elif not disc:
        disc_totals = {TinyTag.get(track).disc_total for track in tracks}
        disc_total = next(iter(disc_totals), "")
        if not disc_total and (
            skip_confirm_disc_overwrite
            or confirm(
                f'Apply default disc and disc total value of "{color("1", bold=True)}"'
                f" to album with missing disc and disc total: {style_album(album)}?"
            )
        ):
            disc = "1"
            disc_total = "1"
            fixable_disc = True
    elif bracket_disc and bracket_disc == disc:
        remove_bracket_disc = True
    remove_bracket_disc = remove_bracket_disc or bool(fixable_disc and bracket_disc)
    return disc, disc_total, fixable_disc, remove_bracket_disc


def get_modify_tracks_query(artist: str, field: str, album_title: str) -> list[str]:
    query = [f"album::^{album_title}$"]
    if field and artist:
        query = [f"{field}::^{artist}$"] + query
    return query


def get_modify_tracks_modification(field: str, new_value: str) -> list[str]:
    return [f"{field}={new_value}"]


def import_album(
    album: str,
    tracks: list[Path],
    import_all: bool,
    as_is: bool,
    skip_confirm_disc_overwrite: bool,
) -> str:
    track_count = len(tracks)
    track_total, track_message = get_track_total(tracks)
    if import_all or track_count == track_total:
        error = "" if beet_import(album) else "escape_error"
        if not as_is and not error:
            album_title = get_album_title(tracks)
            if not album_title:
                album_title = ""
            year, fixable_year = check_year(tracks, album_title)
            artist, field = get_artist_and_field(tracks)
            query = get_modify_tracks_query(artist, field, escape(album_title))
            if fixable_year and year and album_title:
                modification = get_modify_tracks_modification("year", year)
                modify_tracks(query + modification, True, False)
            disc, disc_total, fixable_disc, remove_bracket_disc = check_disc(
                tracks, album_title, skip_confirm_disc_overwrite
            )
            if fixable_disc and album_title:
                if disc:
                    modification = get_modify_tracks_modification("disc", disc)
                    modify_tracks(query + modification, False, False)
                if disc_total:
                    modification = get_modify_tracks_modification(
                        "disctotal", disc_total
                    )
                    modify_tracks(query + modification, True, False)
            if remove_bracket_disc:
                discless_album_title = sub(BRACKET_DISC_REGEX, "", album_title)
                query = [
                    f"album::^{escape(album_title)}$",
                    f"album={discless_album_title}",
                ]
                modify_tracks(query, True, False)
    elif track_message:
        error = track_message
    elif isinstance(track_total, int) and track_count > track_total:
        error = "conflicting_track_totals"
    else:
        error = "missing_tracks"
    return error


def import_albums(
    albums: list[str],
    as_is: bool,
    skip_confirm_disc_overwrite: bool,
    import_all=False,
):
    errors: dict[str, list] = {key: list() for key in ERRORS.keys()}
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
            error = import_album(
                album, tracks, import_all, as_is, skip_confirm_disc_overwrite
            )
            if error:
                errors[error].append(album)
                if error in IMPORTABLE_ERROR_KEYS:
                    importable_error_albums.append(album)
            else:
                imports = True
        if wav_tracks:
            if import_all:
                import_wav_files(album)
                history_add([album.encode()])
                wav_imports += 1
            else:
                errors["wav_files"].append(album)
                importable_error_albums.append(album)
        if not tracks and not wav_tracks:
            errors["no_tracks"].append(album)
    if wav_imports:
        echo(
            f"Imported {wav_imports} {'album' if wav_imports == 1 else 'albums'} in WAV"
            " format."
        )
    if not import_all:
        echo(f"{skipped_count} albums skipped.")
    for key, error_albums in errors.items():
        if error_albums:
            album_string = "Albums" if len(error_albums) > 1 else "Album"
            echo(color(f"{album_string} {key.replace('_', ' ')}:"))
            for album in error_albums:
                echo(f"- {album}")
    return imports, errors, importable_error_albums
