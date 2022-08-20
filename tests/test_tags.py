from dataclasses import dataclass
from typing import Optional

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
    albumartist: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[str] = None
    track_total: Optional[str] = None
    disc: Optional[str] = None
    disc_total: Optional[str] = None


class TestGetAlbumArtist:
    @staticmethod
    def set_mock_get_albumartist(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(albumartist=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_albumartist(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_albumartist("albumartist", monkeypatch)
        albumartist = get_albumartist(tracks)
        assert albumartist == "albumartist"
        self.set_mock_get_albumartist("", monkeypatch)
        albumartist = get_albumartist(tracks)
        assert albumartist == ""


class TestGetArtists:
    @staticmethod
    def set_mock_get_artists(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(artist=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_artists(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_artists("artist", monkeypatch)
        artists = get_artists(tracks)
        assert artists == {"artist"}
        self.set_mock_get_artists("", monkeypatch)
        artists = get_artists(tracks)
        assert artists == {None}


class TestGetAlbumTitle:
    @staticmethod
    def set_mock_get_album_title(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(album=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_album_title(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_album_title("album title", monkeypatch)
        album_title = get_album_title(tracks)
        assert album_title == "album title"
        self.set_mock_get_album_title("", monkeypatch)
        album_title = get_album_title(tracks)
        assert album_title == ""


class TestGetYears:
    @staticmethod
    def set_mock_get_years(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(year=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_years(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_years("2022", monkeypatch)
        years = get_years(tracks)
        assert years == {"2022"}
        self.set_mock_get_years("", monkeypatch)
        years = get_years(tracks)
        assert years == {None}


class TestGetTrackTotals:
    @staticmethod
    def set_mock_get_track_totals(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(track_total=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_track_totals(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_track_totals("10", monkeypatch)
        track_totals = get_track_totals(tracks)
        assert track_totals == {"10"}
        self.set_mock_get_track_totals("", monkeypatch)
        track_totals = get_track_totals(tracks)
        assert track_totals == {None}


class TestGetDiscNumber:
    @staticmethod
    def set_mock_get_disc_number(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(disc=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_disc_number(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_disc_number("5", monkeypatch)
        disc_number = get_disc_number(tracks)
        assert disc_number == "5"
        self.set_mock_get_disc_number("", monkeypatch)
        disc_number = get_disc_number(tracks)
        assert disc_number == ""


class TestGetDiscTOtal:
    @staticmethod
    def set_mock_get_disc_total(value, monkeypatch):
        if value:
            mock_tiny_tag = MockTinyTag(disc_total=value)
        else:
            mock_tiny_tag = MockTinyTag()

        def mock_get(_):
            return mock_tiny_tag

        monkeypatch.setattr(TinyTag, "get", mock_get)

    def test_get_disc_total(self, monkeypatch, tmp_path):
        tracks = [tmp_path]
        self.set_mock_get_disc_total("10", monkeypatch)
        disc_total = get_disc_total(tracks)
        assert disc_total == "10"
        self.set_mock_get_disc_total("", monkeypatch)
        disc_total = get_disc_total(tracks)
        assert disc_total == ""
