from os import system, walk
from pathlib import Path
from pickle import load
from re import Match, escape, search, sub
from typing import Optional

from beets.importer import history_add
from rich.prompt import Prompt

from .config import (
    get_ignored_directories,
    get_music_player,
    get_pickle_file,
    get_shared_directory,
)
from .library import modify_tracks
from .regex import BRACKET_DISC_REGEX, BRACKET_SOLO_INSTRUMENT, BRACKET_YEAR_REGEX
from .style import PrintLevel, print_with_color
from .tags import (
    get_album_title,
    get_albumartist,
    get_artists,
    get_disc_total,
    get_discs,
    get_track_totals,
    get_years,
)

AUDIO_FILE_TYPES = ("*.mp3", "*.Mp3", "*.m4a", "*.flac", "*.aif*")
ESCAPE_ERROR = "escape error"
CONFLICTING_TRACK_TOTALS = "conflicting track totals"
MISSING_TRACK_TOTAL = "missing track total"
MISSING_TRACKS = "missing tracks"
NO_TRACKS = "no tracks"
WAV_FILES = "wav files"
SKIP = "skip"
ERRORS = {
    ESCAPE_ERROR: "Error parsing path name",
    CONFLICTING_TRACK_TOTALS: "Album tracks include more than one track total number",
    MISSING_TRACK_TOTAL: "Album does not contain a track total number",
    MISSING_TRACKS: "Album is missing tracks",
    NO_TRACKS: "Folder does not contain supported audio files",
    WAV_FILES: "Album is in wav format",
}
IMPORTABLE_ERROR_KEYS = [
    CONFLICTING_TRACK_TOTALS,
    MISSING_TRACK_TOTAL,
    MISSING_TRACKS,
    WAV_FILES,
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
        found_files = Path(album).glob(file_type)
        audio_files.extend(found_files)
    return audio_files


def has_wav_tracks(album: str) -> bool:
    wav_tracks = [track for track in Path(album).glob("*.wav")]
    return bool(wav_tracks)


def get_track_total(tracks: list[Path]) -> tuple[Optional[int], str]:
    message = ""
    track_totals = get_track_totals(tracks)
    track_total: Optional[str] | int = next(iter(track_totals), None)
    if track_total is not None:
        track_total = int(track_total)
    if len(track_totals) > 1:
        message = CONFLICTING_TRACK_TOTALS
    elif not track_total:
        message = MISSING_TRACK_TOTAL
    return track_total, message


def is_ignored_directory(album: str) -> bool:
    ignored_directories = get_ignored_directories()
    matching_directories = (
        directory for directory in ignored_directories if directory in album
    )
    return any(matching_directories)


def is_already_imported(album: str) -> bool:
    return album in get_imported_albums()


def get_escaped_album(album: str) -> str:
    single_quote = "'" in album
    double_quote = '"' in album
    if single_quote and double_quote:
        album = album.replace('"', r"\"")
        quote_character = '"'
    else:
        quote_character = "'" if double_quote else '"'
    album = album.replace("$", r"\$")
    return f"{quote_character}{album}{quote_character}"


def beet_import(album: str) -> bool:
    album = get_escaped_album(album)
    try:
        system(f"beet import {album}")
        return True
    except Exception:
        return False


def import_wav_files(album: str):
    music_player = get_music_player()
    system(f"open -a '{music_player}' '{album}'")


def get_artist_and_artist_field_name(
    tracks: list[Path],
) -> tuple[str, str]:
    field = "albumartist"
    artist = ""
    try:
        artist = get_albumartist(tracks)
    except Exception:
        artists = get_artists(tracks)
        if len(artists) > 1:
            field = ""
        else:
            artist = next(iter(artists), artist)
            field = "artist"
    return artist, field


def should_update(
    field: str, bracket_value: str, existing_value: str, album: str
) -> bool:
    return Prompt.ask(
        f"Use bracket {field} [yellow]{bracket_value}[/yellow] instead of"
        f" {field} ([yellow]{existing_value}[/yellow]) for album:"
        f" [blue]{album}[/blue]?"
    )


def get_bracket_number(match: Optional[Match[str]]) -> Optional[str]:
    if not match:
        return None
    group = match.group()
    numeric_characters = [character for character in group if character.isnumeric()]
    return "".join(numeric_characters)


def check_year(tracks: list[Path], album: str, prompt: bool) -> tuple[str, bool]:
    update_year = False
    years = get_years(tracks)
    year = str(next(iter(years), ""))
    single_year = len(years) == 1
    if single_year:
        album = get_album_title(tracks)
        match = search(BRACKET_YEAR_REGEX, album)
        bracket_year = get_bracket_number(match)
        update_with_bracket_year = (
            bracket_year
            and bracket_year != year
            and prompt
            and should_update("year", bracket_year, year, album)
        )
        if update_with_bracket_year and bracket_year:
            year = bracket_year
            update_year = True
    return year, update_year


def check_disc(
    tracks: list[Path],
    album: str,
    skip_confirm_disc_overwrite: bool,
    prompt: bool,
) -> tuple[str, str, bool, bool]:
    update_disc = False
    remove_bracket_disc = False
    discs = get_discs(tracks)
    disc = str(next(iter(discs), ""))
    disc_total = ""
    if album:
        match = search(BRACKET_DISC_REGEX, album)
        bracket_disc = get_bracket_number(match)
    else:
        bracket_disc = None
    update_with_bracket_disc = (
        bracket_disc
        and bracket_disc != disc
        and prompt
        and should_update("disc", bracket_disc, disc, album)
    )
    if update_with_bracket_disc and bracket_disc:
        disc = bracket_disc
        update_disc = True
    elif not disc:
        disc_total = get_disc_total(tracks)
        apply_default_disc = not disc_total and (
            skip_confirm_disc_overwrite
            or prompt
            and Prompt.ask(
                'Apply default disc and disc total value of [bold]"1"[/bold]'
                f" to album with missing disc and disc total: [blue]{album}[/blue]?",
            )
        )
        if apply_default_disc:
            disc = "1"
            disc_total = "1"
            update_disc = True
    elif bracket_disc and bracket_disc == disc:
        remove_bracket_disc = True
    remove_bracket_disc = remove_bracket_disc or bool(update_disc and bracket_disc)
    return disc, disc_total, update_disc, remove_bracket_disc


def has_solo_instrument(artist: str) -> Optional[str]:
    if not artist:
        return None
    match = search(BRACKET_SOLO_INSTRUMENT, artist)
    if not match:
        return None
    return match.group()


def check_artist(
    tracks: list[Path], skip_confirm_artist_overwrite: bool, prompt: bool
) -> tuple[str, bool]:
    update_artist = False
    artists = get_artists(tracks)
    solo_instrument = next(
        (artist for artist in artists if has_solo_instrument(artist)), ""
    )
    update_artist = (
        solo_instrument
        and skip_confirm_artist_overwrite
        or prompt
        and Prompt.ask(
            "Remove bracketed solo instrument indication"
            f" ([blue]{solo_instrument}[/blue]) from the artist field and add to"
            " comments?"
        )
    )
    return solo_instrument, bool(update_artist)


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
    is_complete_album = track_count and track_total and track_count == track_total
    if import_all or is_complete_album:
        album_title = get_album_title(tracks)
        year, update_year = check_year(tracks, album_title, prompt=prompt)
        disc, disc_total, update_disc, remove_bracket_disc = check_disc(
            tracks, album_title, skip_confirm_disc_overwrite, prompt
        )
        solo_instrument, update_artist = check_artist(
            tracks, skip_confirm_artist_overwrite, prompt
        )
        requires_prompt = not update_year or not update_disc or not update_artist
        if not prompt and requires_prompt:
            return SKIP
        error = "" if beet_import(album) else ESCAPE_ERROR
        if error or as_is:
            return error
        artist, field = get_artist_and_artist_field_name(tracks)
        query = get_modify_tracks_query(artist, field, escape(album_title))
        if update_year and year and album_title:
            modification = get_modify_tracks_modification("year", year)
            modify_tracks(query + modification)
        if update_disc and album_title:
            if disc:
                modification = get_modify_tracks_modification("disc", disc)
                modify_tracks(query + modification, album=False)
            if disc_total:
                modification = get_modify_tracks_modification("disctotal", disc_total)
                modify_tracks(query + modification)
        if remove_bracket_disc:
            discless_album_title = sub(BRACKET_DISC_REGEX, "", album_title)
            query = [
                f"album::^{escape(album_title)}$",
                f"album={discless_album_title}",
            ]
            modify_tracks(query)
        if update_artist and solo_instrument:
            artist_without_instrument = sub(
                BRACKET_SOLO_INSTRUMENT, "", solo_instrument
            )
            modification = get_modify_tracks_modification(
                "artist", artist_without_instrument
            )
            modify_tracks(query + modification, album=False)
    elif track_message:
        error = track_message
    elif isinstance(track_total, int) and track_count > track_total:
        error = CONFLICTING_TRACK_TOTALS
    else:
        error = MISSING_TRACKS
    return error


def print_errors(errors: dict):
    for key, error_albums in errors.items():
        if error_albums:
            album_string = "Albums" if len(error_albums) > 1 else "Album"
            print_with_color(f"{album_string} {key}:", style=PrintLevel.INFO)
            for album in error_albums:
                print(f"- {album}")


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
        wav_tracks = has_wav_tracks(album)
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
                errors[WAV_FILES].append(album)
                importable_error_albums.append(album)
            else:
                prompt_skipped_count += 1
        if not tracks and not wav_tracks:
            if prompt:
                errors[NO_TRACKS].append(album)
            else:
                prompt_skipped_count += 1
    if wav_imports:
        print(
            f"Imported {wav_imports} {'album' if wav_imports == 1 else 'albums'} in WAV"
            " format."
        )
    if not import_all:
        print(f"Skipped {skipped_count} previously imported albums.")
    if not prompt:
        print(f"Skipped {prompt_skipped_count} albums requiring prompt.")
    print_errors(errors)
    return imports, errors, importable_error_albums
