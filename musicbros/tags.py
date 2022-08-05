from pathlib import Path

from tinytag import TinyTag

Tracks = list[Path]
Tags = set[str]


def get_album_wide_tag(tags: Tags) -> str:
    return next(iter(tags), "")


def get_albumartist(tracks: Tracks) -> str:
    albumartists = {TinyTag.get(track).albumartist for track in tracks}
    return get_album_wide_tag(albumartists)


def get_artists(tracks: Tracks) -> Tags:
    return {TinyTag.get(track).artist for track in tracks}


def get_album_title(tracks: Tracks) -> str:
    album_titles = {TinyTag.get(track).album for track in tracks}
    return get_album_wide_tag(album_titles)


def get_years(tracks: Tracks) -> Tags:
    return {TinyTag.get(track).year for track in tracks}


def get_track_totals(tracks: Tracks) -> Tags:
    return {TinyTag.get(track).track_total for track in tracks}


def get_discs(tracks: Tracks) -> Tags:
    return {TinyTag.get(track).disc for track in tracks}


def get_disc_total(tracks: Tracks) -> str:
    disc_totals = {TinyTag.get(track).disc_total for track in tracks}
    return get_album_wide_tag(disc_totals)
