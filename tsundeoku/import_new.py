from enum import Enum
from os import system, walk
from pathlib import Path
from pickle import load
from re import escape, search, sub

from beets.importer import history_add
from pync import notify
from rich.console import Console
from rich.markup import escape as rich_escape
from rich.prompt import Confirm
from rich.table import Table

from tsundeoku.reformat import reformat_albums

from .config.config import (
    APP_NAME,
    get_ignored_directories,
    get_loaded_config,
    get_music_player,
    get_pickle_file,
    get_shared_directories,
)
from .library import get_library_tracks, modify_tracks
from .regex import (
    BRACKET_DISC_REGEX,
    BRACKET_YEAR_REGEX,
    SOLO_INSTRUMENT_REGEX,
    YEAR_RANGE_REGEX,
)
from .schedule import send_email, stamp_logs
from .style import stylize
from .tags import (
    Tracks,
    get_album_title,
    get_album_wide_tag,
    get_albumartist,
    get_artists,
    get_disc_number,
    get_disc_total,
    get_track_totals,
    get_years,
)

BeetsQuery = list[str]
YEAR_RANGE_SEPARATORS = {"-", "/"}


class ImportError(Enum):
    ESCAPE_ERROR = "escape error"
    CONFLICTING_TRACK_TOTALS = "conflicting track totals"
    MISSING_TRACK_TOTAL = "missing track total"
    MISSING_TRACKS = "missing tracks"
    NO_TRACKS = "no tracks"
    WAV_FILES = "wav files"
    MISSING_ALBUM_TITLE = "missing album title"
    SKIP = "skip"


IMPORTABLE_ERROR_KEYS = {
    ImportError.CONFLICTING_TRACK_TOTALS,
    ImportError.MISSING_TRACK_TOTAL,
    ImportError.MISSING_TRACKS,
    ImportError.WAV_FILES,
}
AUDIO_FILE_TYPES = ("*.mp3", "*.Mp3", "*.m4a", "*.flac", "*.aif*")


def get_imported_albums() -> set[str]:
    pickle_file = get_pickle_file()
    if not pickle_file:
        return set()
    with open(pickle_file, "rb") as pickle_contents:
        unpickled = load(pickle_contents)["taghistory"]
    return {album[0].decode() for album in unpickled}


def get_albums() -> list[str]:
    shared_directories = get_shared_directories()
    albums: list[str] = []
    if not shared_directories:
        return albums
    for directory in shared_directories:
        albums.extend(
            [root for root, dirs, files in walk(directory) if files and not dirs]
        )
    return albums


def get_tracks(album: str) -> Tracks:
    audio_files: Tracks = []
    for file_type in AUDIO_FILE_TYPES:
        found_files = Path(album).glob(file_type)
        audio_files.extend(found_files)
    return audio_files


def has_wav_tracks(album: str) -> bool:
    wav_tracks = [track for track in Path(album).glob("*.wav")]
    return bool(wav_tracks)


def get_track_total(tracks: Tracks) -> int | ImportError:
    track_totals = get_track_totals(tracks)
    track_total: str | None = get_album_wide_tag(track_totals)
    if not track_total:
        return ImportError.MISSING_TRACK_TOTAL
    if len(track_totals) > 1:
        return ImportError.CONFLICTING_TRACK_TOTALS
    return int(track_total)


def is_in_ignored_directory(album: str) -> bool:
    ignored_directories = get_ignored_directories()
    matching_directories = (
        directory for directory in ignored_directories if str(directory) in album
    )
    return any(matching_directories)


def is_already_imported(album: str) -> bool:
    get_loaded_config()
    return album in get_imported_albums()


def get_escaped_album(album: str) -> str:
    single_quote = "'"
    double_quote = '"'
    escaped_double_quote = r"\""
    has_single_quote = single_quote in album
    has_double_quote = double_quote in album
    if has_single_quote and has_double_quote:
        album = album.replace(double_quote, escaped_double_quote)
        quote_character = double_quote
    else:
        quote_character = single_quote if has_double_quote else double_quote
    album = album.replace("$", r"\$")
    return f"{quote_character}{album}{quote_character}"


def beet_import(album: str) -> ImportError | None:
    album = get_escaped_album(album)
    try:
        system(f"beet import {album}")
        return None
    except Exception:
        return ImportError.ESCAPE_ERROR


def import_wav_files(album: str):
    music_player = get_music_player()
    system(f"open -a '{music_player}' '{album}'")


def get_artist_and_artist_field_name(
    tracks: Tracks,
) -> tuple[str, str]:
    artist_field_type = "albumartist"
    artist = ""
    try:
        artist = get_albumartist(tracks)
    except Exception:
        artists = get_artists(tracks)
        if len(artists) > 1:
            artist_field_type = ""
        else:
            artist = get_album_wide_tag(artists)
            artist_field_type = "artist"
    return artist, artist_field_type


def should_update(
    field: str, bracket_value: str, existing_value: str | None, album_title: str
) -> bool:
    bracket_value = stylize(bracket_value, ["bold", "yellow"])
    existing_value = existing_value or ""
    existing_value = stylize(existing_value, ["bold", "yellow"])
    album_title = stylize(rich_escape(album_title), "blue")
    return Confirm.ask(
        f"Use bracket {field} {bracket_value} instead of"
        f" {field} ({existing_value}) for album:"
        f" {album_title}?"
    )


def is_bracket_number(character: str, year_format=False) -> bool:
    if character.isnumeric() or year_format and character in YEAR_RANGE_SEPARATORS:
        return True
    return False


def get_bracket_numbers(regex: str, album_title: str, year_range=False) -> str | None:
    match = search(regex, album_title)
    if not match:
        return None
    group = match.group()
    numeric_characters = [
        character
        for character in group
        if is_bracket_number(character, year_format=year_range)
    ]
    return "".join(numeric_characters)


def get_new_year(tracks: Tracks, album_title: str, allow_prompt: bool) -> str | None:
    years = get_years(tracks)
    single_year = len(years) == 1
    if not single_year:
        return None
    bracket_year = get_bracket_numbers(BRACKET_YEAR_REGEX, album_title)
    year = get_album_wide_tag(years)
    if not bracket_year or bracket_year == year:
        return None
    if not allow_prompt:
        raise Exception
    update_year = should_update("year", bracket_year, year, album_title)
    if not update_year:
        return None
    return bracket_year


def get_year_range_comment(tracks: Tracks, album_title: str) -> str | None:
    years = get_years(tracks)
    bracket_year = get_bracket_numbers(YEAR_RANGE_REGEX, album_title, year_range=True)
    if not bracket_year:
        return None
    year_range = False
    for character in YEAR_RANGE_SEPARATORS:
        if character in bracket_year:
            year_range = True
            break
    if not year_range:
        return None
    start_year = bracket_year[:4]
    if start_year in years or all(bool(year) for year in years):
        return None
    return bracket_year


def get_new_disc_numbers(
    tracks: Tracks, album_title: str, ask_before_disc_update: bool, allow_prompt: bool
) -> tuple[str | None, str | None, bool]:
    new_disc_number = None
    new_disc_total = None
    remove_bracket_disc = False
    disc_number: str | None = get_disc_number(tracks)
    bracket_disc = get_bracket_numbers(BRACKET_DISC_REGEX, album_title)
    if not bracket_disc:
        if disc_number:
            new_disc_number = None
        else:
            disc_total = get_disc_total(tracks)
            skip = ask_before_disc_update and not allow_prompt
            if not disc_total:
                if skip:
                    raise Exception
                if (
                    not ask_before_disc_update
                    or allow_prompt
                    and Confirm.ask(
                        "Apply default disc and disc total value of"
                        f' {stylize("1", ["bold", "yellow"])} to album with'
                        " missing disc and disc total:"
                        f" {stylize(rich_escape(album_title), 'blue')}?"
                    )
                ):
                    new_disc_number = "1"
                    new_disc_total = "1"
                else:
                    new_disc_number = None
        return new_disc_number, new_disc_total, remove_bracket_disc
    remove_bracket_disc = True
    if bracket_disc == disc_number:
        new_disc_number = None
    else:
        if not allow_prompt:
            raise Exception
        if should_update("disc", bracket_disc, disc_number, album_title):
            new_disc_number = bracket_disc
        else:
            new_disc_number = None
            remove_bracket_disc = False
    return new_disc_number, new_disc_total, remove_bracket_disc


def has_solo_instrument(artist: str | None) -> bool:
    if not artist:
        return False
    match = search(SOLO_INSTRUMENT_REGEX, artist)
    if not match:
        return False
    return bool(match.group())


def get_artists_to_update(
    tracks: Tracks, ask_before_artist_update: bool, allow_prompt: bool
) -> list[str | None]:
    artists = get_artists(tracks)
    artists_with_instruments = [
        artist for artist in artists if has_solo_instrument(artist)
    ]
    artists_to_update: list[str | None] = []
    if not artists_with_instruments:
        return artists_to_update
    for artist_with_instrument in artists_with_instruments:
        skip = ask_before_artist_update and not allow_prompt
        if skip:
            raise Exception
        artist_with_instrument = artist_with_instrument or ""
        stylized_artist_with_instrument = stylize(
            artist_with_instrument, ["bold", "yellow"]
        )
        if (
            not ask_before_artist_update
            or allow_prompt
            and Confirm.ask(
                "Remove bracketed solo instrument indication"
                f" {stylized_artist_with_instrument} from the"
                " artist field and add to comments?"
            )
        ):
            artists_to_update.append(artist_with_instrument)
    return artists_to_update


def get_modify_tracks_query(
    album_title: str, artist_field_type: str, artist: str
) -> BeetsQuery:
    album_title = escape(album_title)
    query = [f"album::^{album_title}$"]
    if artist_field_type and artist:
        query = [f"{artist_field_type}::^{artist}$"] + query
    return query


def get_modification(field: str, new_value: str) -> BeetsQuery:
    return [f"{field}={new_value}"]


def get_bracket_year_range(album_title: str) -> str:
    match = search(SOLO_INSTRUMENT_REGEX, album_title)
    if not match:
        return ""
    return match.group()


def get_bracket_solo_instrument(artist: str) -> str:
    match = search(SOLO_INSTRUMENT_REGEX, artist)
    if not match:
        return ""
    return match.group()


def add_to_comments(artist: str, album_title: str, value: str):
    tracks = get_library_tracks(artist, album_title)
    for track in tracks:
        comments = track.comments
        if comments:
            comments = f"{comments}; {value}"
        else:
            comments = value
        artist = escape(artist)
        album_title = escape(album_title)
        title = escape(track.title)
        artist_query = f"artist::^{artist}$"
        album_query = f"album::^{album_title}$"
        title_query = f"title::^{title}$"
        query = [artist_query, album_query, title_query]
        modification = get_modification("comments", comments)
        modify_tracks(query + modification, album=False)


def add_year_range_to_comments(artist: str, album_title: str, value: str):
    add_to_comments(artist, album_title, value)


def add_solo_instrument_to_comments(artist: str, album_title: str):
    solo_instrument = get_bracket_solo_instrument(artist).strip()
    add_to_comments(artist, album_title, solo_instrument)


def import_album(
    album: str,
    tracks: Tracks,
    import_all: bool,
    reformat: bool,
    ask_before_disc_update: bool,
    ask_before_artist_update: bool,
    allow_prompt: bool,
) -> ImportError | None:
    track_count = len(tracks)
    track_total = get_track_total(tracks)
    if isinstance(track_total, ImportError) and not import_all:
        return track_total
    is_complete_album = track_count and track_count == track_total
    if not is_complete_album and not import_all:
        if isinstance(track_total, int) and track_count > track_total:
            return ImportError.CONFLICTING_TRACK_TOTALS
        return ImportError.MISSING_TRACKS
    album_title = get_album_title(tracks)
    if not album_title:
        return ImportError.MISSING_ALBUM_TITLE
    if not reformat:
        return beet_import(album)
    try:
        new_year = get_new_year(tracks, album_title, allow_prompt=allow_prompt)
        year_range_comment = None
        if not new_year:
            year_range_comment = get_year_range_comment(tracks, album_title)
        new_disc_number, new_disc_total, remove_bracket_disc = get_new_disc_numbers(
            tracks, album_title, ask_before_disc_update, allow_prompt
        )
        artists_to_update = get_artists_to_update(
            tracks, ask_before_artist_update, allow_prompt
        )
    except Exception:
        return ImportError.SKIP
    error = beet_import(album)
    if error:
        return error
    artist, artist_field_type = get_artist_and_artist_field_name(tracks)
    query = get_modify_tracks_query(album_title, artist_field_type, artist)
    if new_year:
        modification = get_modification("year", new_year)
        modify_tracks(query + modification)
    if year_range_comment:
        add_year_range_to_comments(artist, album_title, year_range_comment)
    if new_disc_number:
        modification = get_modification("disc", new_disc_number)
        modify_tracks(query + modification, album=False)
    if new_disc_total:
        modification = get_modification("disctotal", new_disc_total)
        modify_tracks(query + modification)
    if remove_bracket_disc:
        discless_album_title = sub(BRACKET_DISC_REGEX, "", album_title)
        modification = get_modification("album", discless_album_title)
        modify_tracks(query + modification)
    for artist_with_instrument in artists_to_update:
        artist_with_instrument = artist_with_instrument or ""
        add_solo_instrument_to_comments(artist_with_instrument, album_title)
        artist_without_instrument = sub(
            SOLO_INSTRUMENT_REGEX, "", artist_with_instrument
        )
        modification = get_modification("artist", artist_without_instrument)
        modify_tracks(query + modification, album=False)
    return error


def import_albums(
    albums: list[str],
    reformat: bool,
    ask_before_disc_update: bool,
    ask_before_artist_update: bool,
    import_all: bool,
    allow_prompt: bool,
    is_scheduled_run: bool,
):
    errors: dict[ImportError, list] = {import_error: [] for import_error in ImportError}
    imports = False
    wav_imports = 0
    skipped_count = 0
    prompt_skipped_count = 0
    importable_error_albums = []
    albums = [album for album in albums if not is_in_ignored_directory(album)]
    for album in albums:
        if is_already_imported(album):
            if not import_all:
                skipped_count += 1
            continue
        tracks = get_tracks(album)
        wav_tracks = has_wav_tracks(album)
        if tracks:
            error = import_album(
                album,
                tracks,
                import_all,
                reformat,
                ask_before_disc_update,
                ask_before_artist_update,
                allow_prompt=allow_prompt,
            )
            if error:
                if allow_prompt:
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
            elif allow_prompt:
                errors[ImportError.WAV_FILES].append(album)
                importable_error_albums.append(album)
            else:
                prompt_skipped_count += 1
        if not tracks and not wav_tracks:
            if allow_prompt:
                errors[ImportError.NO_TRACKS].append(album)
            else:
                prompt_skipped_count += 1
    if wav_imports:
        album_plural = "album" if wav_imports == 1 else "albums"
        print(f"Imported {wav_imports} {album_plural} in WAV format.")
    if not import_all:
        print(f"Skipped {skipped_count} previously imported albums.")
    if not allow_prompt:
        print(f"Skipped {prompt_skipped_count} albums requiring prompt.")
    if any(errors.values()):
        current_errors = [(key, value) for key, value in errors.items() if value]
        table = Table("Index", "Album", "Error", title="Errors")
        index = 0
        for error_name, error_albums in current_errors:
            for album in error_albums:
                shared_directories = get_shared_directories()
                for shared_directory in shared_directories:
                    album = album.replace(str(shared_directory), "")
                index = index + 1
                table.add_row(str(index), album, error_name.value)
        Console().print(table)
    if is_scheduled_run:
        config = get_loaded_config()
        email_on = config.notifications.email_on
        system_on = config.notifications.system_on
        if email_on or system_on:
            error_album_count = (
                sum(len(value) for value in errors.values()) + prompt_skipped_count
            )
            if error_album_count:
                contents = (
                    f"{error_album_count} albums cannot be automatically imported."
                )
                if email_on:
                    send_email(contents)
                if system_on:
                    notify(contents, title=APP_NAME)
    return imports, errors, importable_error_albums


def import_new_albums(
    albums: list[str] | None,
    reformat: bool | None,
    ask_before_disc_update: bool | None,
    ask_before_artist_update: bool | None,
    allow_prompt: bool | None,
    is_scheduled_run=False,
):
    if is_scheduled_run:
        stamp_logs()
    print("Importing newly added albums...")
    config = get_loaded_config()
    import_settings = config.import_new
    if reformat is None:
        reformat = import_settings.reformat
    if ask_before_disc_update is None:
        ask_before_disc_update = import_settings.ask_before_disc_update
    if ask_before_artist_update is None:
        ask_before_artist_update = import_settings.ask_before_artist_update
    if allow_prompt is None:
        allow_prompt = import_settings.allow_prompt
    first_time = False
    if not albums:
        first_time = True
        albums = get_albums()
    import_all = not first_time
    imports, errors, importable_error_albums = import_albums(
        albums,
        reformat,
        ask_before_disc_update,
        ask_before_artist_update,
        import_all,
        allow_prompt,
        is_scheduled_run,
    )
    if imports and reformat:
        reformat_settings = config.reformat
        remove_bracket_years = reformat_settings.remove_bracket_years
        remove_bracket_instruments = reformat_settings.remove_bracket_instruments
        expand_abbreviations = reformat_settings.expand_abbreviations
        reformat_albums(
            remove_bracket_years, remove_bracket_instruments, expand_abbreviations
        )
    if (
        not is_scheduled_run
        and first_time
        and errors
        and importable_error_albums
        and Confirm.ask("Would you like to import all albums anyway?")
    ):
        import_new_albums(
            albums=importable_error_albums,
            reformat=reformat,
            ask_before_disc_update=ask_before_disc_update,
            ask_before_artist_update=ask_before_artist_update,
            allow_prompt=allow_prompt,
        )
