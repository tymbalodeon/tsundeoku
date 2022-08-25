from dataclasses import dataclass

from tinytag import TinyTag

from musicbros.tags import (
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


def test_get_albumartist(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_albumartist)
    albumartist = get_albumartist(tracks)
    assert albumartist == "albumartist"
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    albumartist = get_albumartist(tracks)
    assert albumartist == ""


def test_get_artists(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_artist)
    artists = get_artists(tracks)
    assert artists == {"artist"}
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    artists = get_artists(tracks)
    assert artists == {None}


def test_get_album_title(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_album)
    album_title = get_album_title(tracks)
    assert album_title == "album"
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    album_title = get_album_title(tracks)
    assert album_title == ""


def test_get_years(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_year)
    years = get_years(tracks)
    assert years == {"2022"}
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    years = get_years(tracks)
    assert years == {None}


def test_get_track_totals(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_track_totals)
    track_totals = get_track_totals(tracks)
    assert track_totals == {"10"}
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    track_totals = get_track_totals(tracks)
    assert track_totals == {None}


def test_get_disc_number(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_disc)
    disc_number = get_disc_number(tracks)
    assert disc_number == "5"
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    disc_number = get_disc_number(tracks)
    assert disc_number == ""


def test_get_disc_total(monkeypatch, tmp_path):
    tracks = [tmp_path]
    monkeypatch.setattr(TinyTag, "get", mock_get_disc_total)
    disc_total = get_disc_total(tracks)
    assert disc_total == "10"
    monkeypatch.setattr(TinyTag, "get", mock_get_none)
    disc_total = get_disc_total(tracks)
    assert disc_total == ""
