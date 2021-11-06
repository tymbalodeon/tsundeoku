import pickle
from glob import glob
from os import walk

from tinytag import TinyTag
from typer import colors, echo, secho, style

from .config import get_config_option, get_config_options

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


def get_album_dirs():
    return [
        root
        for root, dirs, files in walk(get_config_option("shared_directory"))
        if files and not dirs
    ]


def get_audio_files():
    audio_file_types = (".mp3", ".m4a", ".flac")
    audio_files = list()
    for file_type in audio_file_types:
        audio_files.extend(glob(file_type))
    return audio_files


def get_track_total(album, track):
    path = f"{album}/{track}"
    tags = TinyTag.get(path)
    if tags.track_total or tags.track_total == "0":
        return int(tags.track_total)
    else:
        return tags.track_total


def check_track_totals(album, tracks):
    total = 0
    for track in tracks:
        track_total = get_track_total(album, track)
        if not track_total:
            return -3
        elif total == 0:
            total = track_total
        elif total != track_total:
            return -1
    return total


def set_quote(album):
    quote = None
    if "'" and '"' in album:
        return quote
    elif '"' in album:
        quote = "'"
        return quote
    else:
        quote = '"'
        return quote


def is_already_imported(album):
    return album in get_imported_albums()


def import_or_get_errors(album):
    errors = list()
    albums = list()
    skipped = False
    imports = False
    audio_files = get_audio_files()
    RESULT = check_track_totals(album, audio_files)
    QUOTE = set_quote(album)
    IMPORTED = is_already_imported(album)
    if len(audio_files) == 0:
        errors.append(
            "\n- Folder is empty or audio is in wav format (please wait"
            f' for sync or resolve manually): "{album}"'
        )
    elif RESULT >= 0:
        if len(audio_files) == RESULT:
            if not QUOTE:
                if not IMPORTED:
                    errors.append(
                        "\n- Annoyingly named directory (please resolve"
                        f' manually): "{album}"'
                    )
                else:
                    skipped = True
            else:
                if not IMPORTED:
                    system(f"beet import {QUOTE}{album}{QUOTE}")
                    imports = True
                else:
                    skipped = True
        elif len(audio_files) > RESULT:
            if not IMPORTED:
                errors.append(
                    "\n- Possible multi-disc album detected (please"
                    f' resolve manually): "{album}"'
                )
                albums.append(album)
            else:
                skipped = True
        else:
            if not IMPORTED:
                errors.append(
                    "\n- Missing tracks (please wait for sync or resolve"
                    f' manually): "{album}"\n\tTrack total: {RESULT}'
                )
                albums.append(album)
            else:
                skipped = True
    else:
        if RESULT == -1:
            if not IMPORTED:
                errors.append(
                    "\n- Possible multi-disc album detected (please"
                    f' resolve manually): "{album}"'
                )
                albums.append(album)
            else:
                skipped = True
        elif RESULT == -2:
            if not IMPORTED:
                errors.append(
                    "\n- Filetype(s) not recognized (please resolve"
                    f' manually): "{album}"'
                )
                albums.append(album)
            else:
                skipped = True
        elif RESULT == -3:
            if not IMPORTED:
                errors.append(
                    "\n- Album does not contain a track total number"
                    f' (please resolve manually): "{album}"'
                )
                albums.append(album)
            else:
                skipped = True
    return errors, skipped, imports, albums


def import_complete_albums(albums):
    final_errors = list()
    final_skipped = 0
    final_imports = False
    returns_errors = False
    bulk_fix_albums = list()
    skip_directories = get_config_option("skip_directories")
    for album in albums:
        if skip_directories in album:
            continue
        else:
            errors, skipped, imports, error_albums = import_or_get_errors(album)
            if imports:
                final_imports = True
            if skipped:
                final_skipped += 1
            if len(errors) > 0:
                for error in errors:
                    final_errors.append(error)
                for album in error_albums:
                    bulk_fix_albums.append(album)
    print(f"{final_skipped} albums skipped.")
    if len(final_errors) > 0:
        for error in final_errors:
            print(error)
        returns_errors = True
    return final_imports, returns_errors, bulk_fix_albums
