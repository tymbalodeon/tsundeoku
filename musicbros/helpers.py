"""track level incremental import"""

import os
import pickle
from tinytag import TinyTag

INCOMING_FOLDER = "/Users/rrosen/Dropbox/Ralph-MichaelC/"
PICKLE_FILE = "/Users/rrosen/.config/beets/state.pickle"
WARNING = "\033[93m"
ENDC = "\033[0m"


def unpickle_to_set(path):
    raw = open(path, "rb")
    unpickle = pickle.load(raw)
    unpickle = unpickle["taghistory"]
    albums = set()
    for album in unpickle:
        albums.add(album[0].decode())
    raw.close()
    return albums


IMPORTED_ALBUMS = unpickle_to_set(PICKLE_FILE)


def get_album_dirs(path):
    albums = list()
    for root, dirs, files in os.walk(INCOMING_FOLDER):
        if files and not dirs:
            albums.append(root)
    return albums


NEW_ALBUMS = get_album_dirs(INCOMING_FOLDER)


def is_audio_file(file):
    return file.lower().endswith((".mp3", ".m4a", ".flac"))


def is_image_file(file):
    return file.lower().endswith((".jpeg", ".jpg", ".pdf", ".docx"))


def get_track_total(album, track):
    path = f"{album}/{track}"
    tags = TinyTag.get(path)
    if tags.track_total or tags.track_total == "0":
        return int(tags.track_total)
    else:
        return tags.track_total


def check_track_totals(album, tracks):
    total = 0
    contains_audio = False
    for track in tracks:
        if is_audio_file(track):
            contains_audio = True
            track_total = get_track_total(album, track)
            if not track_total:
                return -3
            elif total == 0:
                total = track_total
            elif total != track_total:
                return -1
    if not contains_audio:
        for track in tracks:
            if not is_image_file(track):
                return -2
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
    if album in IMPORTED_ALBUMS:
        return True
    else:
        return False


def import_or_get_errors(album):
    errors = list()
    albums = list()
    skipped = False
    imports = False
    for root, dirs, files in os.walk(album):
        AUDIO_FILES = [track for track in files if is_audio_file(track)]
        RESULT = check_track_totals(album, files)
        QUOTE = set_quote(album)
        IMPORTED = is_already_imported(album)
        if len(AUDIO_FILES) == 0:
            errors.append(
                f"\n{WARNING}- Folder is empty or audio is in wav format (please wait"
                f' for sync or resolve manually): {ENDC}"{album}"'
            )
        elif RESULT >= 0:
            if len(AUDIO_FILES) == RESULT:
                if not QUOTE:
                    if not IMPORTED:
                        errors.append(
                            f"\n{WARNING}- Annoyingly named directory (please resolve"
                            f' manually): {ENDC}"{album}"'
                        )
                    else:
                        skipped = True
                else:
                    if not IMPORTED:
                        os.system(f"beet import {QUOTE}{album}{QUOTE}")
                        imports = True
                    else:
                        skipped = True
            elif len(AUDIO_FILES) > RESULT:
                if not IMPORTED:
                    errors.append(
                        f"\n{WARNING}- Possible multi-disc album detected (please"
                        f' resolve manually): {ENDC}"{album}"'
                    )
                    albums.append(album)
                else:
                    skipped = True
            else:
                if not IMPORTED:
                    errors.append(
                        f"\n{WARNING}- Missing tracks (please wait for sync or resolve"
                        f' manually): {ENDC}"{album}"\n\tTrack total: {RESULT}'
                    )
                    albums.append(album)
                else:
                    skipped = True
        else:
            if RESULT == -1:
                if not IMPORTED:
                    errors.append(
                        f"\n{WARNING}- Possible multi-disc album detected (please"
                        f' resolve manually): {ENDC}"{album}"'
                    )
                    albums.append(album)
                else:
                    skipped = True
            elif RESULT == -2:
                if not IMPORTED:
                    errors.append(
                        f"\n{WARNING}- Filetype(s) not recognized (please resolve"
                        f' manually): {ENDC}"{album}"'
                    )
                    albums.append(album)
                else:
                    skipped = True
            elif RESULT == -3:
                if not IMPORTED:
                    errors.append(
                        f"\n{WARNING}- Album does not contain a track total number"
                        f' (please resolve manually): {ENDC}"{album}"'
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
    for album in albums:
        if not album.startswith(
            "/Users/rrosen/Dropbox/Ralph-MichaelC/ZZ-ALBUM COVER ART--DO NOT DELETE"
        ):
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


#!/usr/bin/env python3
