from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pytest import MonkeyPatch, mark
from tinytag import TinyTag

from tsundeoku.tags import (
    get_album_title,
    get_albumartist,
    get_artists,
    get_disc_number,
    get_disc_total,
    get_track_totals,
    get_years,
)


@dataclass
class MockTinyTag:
    albumartist: str | None = None
    artist: str | None = None
    album: str | None = None
    year: str | None = None
    track_total: str | None = None
    disc: str | None = None
    disc_total: str | None = None


def mock_get_none(_) -> MockTinyTag:
    return MockTinyTag()


def mock_get_albumartist(_) -> MockTinyTag:
    return MockTinyTag(albumartist="albumartist")


def mock_get_artist(_) -> MockTinyTag:
    return MockTinyTag(artist="artist")


def mock_get_album(_) -> MockTinyTag:
    return MockTinyTag(album="album")


def mock_get_year(_) -> MockTinyTag:
    return MockTinyTag(year="2022")


def mock_get_track_totals(_) -> MockTinyTag:
    return MockTinyTag(track_total="10")


def mock_get_disc(_) -> MockTinyTag:
    return MockTinyTag(disc="5")


def mock_get_disc_total(_) -> MockTinyTag:
    return MockTinyTag(disc_total="10")


MockGetter = Callable[[Any], MockTinyTag]


def get_args(
    mock_getter: MockGetter, expected_value: str, empty_string=True
) -> list[tuple[MockGetter, str | None]]:
    if empty_string:
        none_value = ""
    else:
        none_value = None
    return [(mock_getter, expected_value), (mock_get_none, none_value)]


@mark.parametrize(
    "mock_getter, expected_value", get_args(mock_get_albumartist, "albumartist")
)
def test_get_albumartist(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    albumartist = get_albumartist(tracks)
    assert albumartist == expected_value


@mark.parametrize(
    "mock_getter, expected_value",
    get_args(mock_get_artist, "artist", empty_string=False),
)
def test_get_artists(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    artists = get_artists(tracks)
    assert artists == {expected_value}


@mark.parametrize("mock_getter, expected_value", get_args(mock_get_album, "album"))
def test_get_album_title(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    album_title = get_album_title(tracks)
    assert album_title == expected_value


@mark.parametrize(
    "mock_getter, expected_value", get_args(mock_get_year, "2022", empty_string=False)
)
def test_get_years(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    years = get_years(tracks)
    assert years == {expected_value}


@mark.parametrize(
    "mock_getter, expected_value",
    get_args(mock_get_track_totals, "10", empty_string=False),
)
def test_get_track_totals(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    track_totals = get_track_totals(tracks)
    assert track_totals == {expected_value}


@mark.parametrize("mock_getter, expected_value", get_args(mock_get_disc, "5"))
def test_get_disc_number(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    disc_number = get_disc_number(tracks)
    assert disc_number == expected_value


@mark.parametrize("mock_getter, expected_value", get_args(mock_get_disc_total, "10"))
def test_get_disc_total(
    mock_getter: MockGetter,
    expected_value: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_getter)
    disc_total = get_disc_total(tracks)
    assert disc_total == expected_value
