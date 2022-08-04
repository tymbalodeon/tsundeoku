from os import system, walk
from pathlib import Path
from pickle import load
from re import Match, escape, search, sub
from typing import Optional

from beets.importer import history_add
from tinytag import TinyTag
from typer import confirm, echo

from .config import (
    get_ignored_directories,
    get_music_player,
    get_pickle_file,
    get_shared_directory,
)
from .library import modify_tracks
from .regex import BRACKET_DISC_REGEX, BRACKET_SOLO_INSTRUMENT, BRACKET_YEAR_REGEX
from .style import Color, color

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
    pickle_file = get_pickle_file()
    with open(pickle_file, "rb") as raw_pickle:
        unpickled = load(raw_pickle)["taghistory"]
        return {album[0].decode() for album in unpickled}


def get_album_directories() -> list[str]:
    shared_directory = get_shared_directory()
    return [root for root, dirs, files in walk(shared_directory) if files and not dirs]


def get_tracks(album: str) -> list[Path]:
    audio_files: list[Path] = []
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
    for directory in get_ignored_directories():
        if directory in album:
            return True
    return False


def is_already_imported(album: str) -> bool:
    return album in get_imported_albums()


def get_single_or_double_quote(album: str) -> Optional[str]:
    if "'" in album and '"' in album:
        return None
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
    try:
        system(f"beet import {quote_character}{album}{quote_character}")
        return True
    except Exception:
        return False


def import_wav_files(album: str):
    music_player = get_music_player()
    system(f"open -a '{music_player}' '{album}'")


def get_album_title(tracks: list[Path]) -> str:
    return next(iter({TinyTag.get(track).album for track in tracks}), "")


def get_artist_and_artist_field_name(tracks: list[Path]) -> tuple[str, str]:
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


def get_bracket_number(match: Optional[Match[str]]) -> Optional[str]:
    if not match:
        return None
    group = match.group()
    numeric_characters = [character for character in group if character.isnumeric()]
    return "".join(numeric_characters)


def check_year(
    tracks: list[Path], album: Optional[str], prompt: bool
) -> tuple[Optional[str], bool]:
    fixable_year = False
    years = {TinyTag.get(track).year for track in tracks}
    year = next(iter(years), "")
    if len(years) == 1:
        album = str(next(iter({TinyTag.get(track).album for track in tracks}), ""))
        match = search(BRACKET_YEAR_REGEX, album)
        bracket_year = get_bracket_number(match)
        if (
            bracket_year
            and bracket_year != year
            and prompt
            and should_update("year", bracket_year, year, album)
        ):
            year = bracket_year
            fixable_year = True
    return year, fixable_year


def check_disc(
    tracks: list[Path], album: str, skip_confirm_disc_overwrite: bool, prompt: bool
) -> tuple[Optional[str], Optional[str], bool, bool]:
    fixable_disc = False
    remove_bracket_disc = False
    discs = {TinyTag.get(track).disc for track in tracks}
    disc = next(iter(discs), "")
    disc_total = None
    match = search(BRACKET_DISC_REGEX, album)
    bracket_disc = get_bracket_number(match)
    if (
        bracket_disc
        and bracket_disc != disc
        and prompt
        and should_update("disc", bracket_disc, disc, album)
    ):
        disc = bracket_disc
        fixable_disc = True
    elif not disc:
        disc_totals = {TinyTag.get(track).disc_total for track in tracks}
        disc_total = next(iter(disc_totals), None)
        if not disc_total and (
            skip_confirm_disc_overwrite
            or prompt
            and confirm(
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


def has_solo_instrument(artist: str) -> Optional[str]:
    match = search(BRACKET_SOLO_INSTRUMENT, artist)
    if not match:
        return None
    return match.group()


def check_artist(
    tracks: list[Path], skip_confirm_artist_overwrite: bool, prompt: bool
) -> Optional[str]:
    artists = {TinyTag.get(track).artist for track in tracks}
    solo_instrument = next(
        (artist for artist in artists if has_solo_instrument(artist)), None
    )
    return solo_instrument


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
    skip_confirm_artist_overwrite: bool,
    prompt: bool,
) -> str:
    track_count = len(tracks)
    track_total, track_message = get_track_total(tracks)
    if import_all or track_count == track_total:
        album_title = get_album_title(tracks)
        year, fixable_year = check_year(tracks, album_title, prompt=prompt)
        disc, disc_total, fixable_disc, remove_bracket_disc = check_disc(
            tracks, album_title, skip_confirm_disc_overwrite, prompt
        )
        solo_instrument = check_artist(tracks, skip_confirm_artist_overwrite, prompt)
        if solo_instrument:
            pass
        not_fixable = not fixable_year or not fixable_disc
        if not prompt and not_fixable:
            return "skip"
        error = "" if beet_import(album) else "escape_error"
        if error or as_is:
            return error
        artist, field = get_artist_and_artist_field_name(tracks)
        query = get_modify_tracks_query(artist, field, escape(album_title))
        if fixable_year and year and album_title:
            modification = get_modify_tracks_modification("year", year)
            modify_tracks(query + modification, True, False)
        if fixable_disc and album_title:
            if disc:
                modification = get_modify_tracks_modification("disc", disc)
                modify_tracks(query + modification, False, False)
            if disc_total:
                modification = get_modify_tracks_modification("disctotal", disc_total)
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
    skip_confirm_artist_overwrite: bool,
    import_all=False,
    prompt=True,
):
    errors: dict[str, list] = {key: [] for key in ERRORS.keys()}
    imports = False
    wav_imports = 0
    skipped_count = 0
    prompt_skipped_count = 0
    importable_error_albums = []
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
                album,
                tracks,
                import_all,
                as_is,
                skip_confirm_disc_overwrite,
                skip_confirm_artist_overwrite,
                prompt=prompt,
            )
            if error:
                if prompt:
                    errors[error].append(album)
                    if error in IMPORTABLE_ERROR_KEYS:
                        importable_error_albums.append(album)
                else:
                    prompt_skipped_count += 1
            else:
                imports = True
        if wav_tracks:
            if import_all:
                import_wav_files(album)
                history_add([album.encode()])
                wav_imports += 1
            elif prompt:
                errors["wav_files"].append(album)
                importable_error_albums.append(album)
            else:
                prompt_skipped_count += 1
        if not tracks and not wav_tracks:
            if prompt:
                errors["no_tracks"].append(album)
            else:
                prompt_skipped_count += 1
    if wav_imports:
        echo(
            f"Imported {wav_imports} {'album' if wav_imports == 1 else 'albums'} in WAV"
            " format."
        )
    if not import_all:
        echo(f"Skipped {skipped_count} previously imported albums.")
    if not prompt:
        echo(f"Skipped {prompt_skipped_count} albums requiring prompt.")
    for key, error_albums in errors.items():
        if error_albums:
            album_string = "Albums" if len(error_albums) > 1 else "Album"
            echo(color(f"{album_string} {key.replace('_', ' ')}:"))
            for album in error_albums:
                echo(f"- {album}")
    return imports, errors, importable_error_albums
