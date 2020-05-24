from datetime import date
from os.path import expanduser
from pprint import pprint
from shutil import copyfileobj
import subprocess
from typing import *
import eyed3
from dotenv import load_dotenv
from os import makedirs, path
import re
from spotipy import Spotify, prompt_for_user_token
import requests


class Track(NamedTuple):
    artist: str
    title: str
    album: Optional[str] = None


class TrackSpotify(NamedTuple):
    artists: List[str]
    title: str
    album: str
    total_tracks: int
    release_date: Optional[date]
    track_number: int
    duration: float  # in seconds
    cover_art_url: str

    @property
    def cover_art_filepath(self) -> str:
        return cover_art_cache(self.cover_art_url)

    @property
    def artist(self) -> str:
        return self.artists[0]

    def to_tsv(self) -> str:
        return "\t".join((self.artist, self.title, self.album))


def get_spotify_token() -> str:
    dotenv_path = path.join(path.abspath(path.dirname(path.dirname(__file__))), ".env")
    load_dotenv(dotenv_path)
    # username = input("username = ")
    username = "phelng"
    token = prompt_for_user_token(
        username,
        "user-library-read streaming user-read-currently-playing user-read-playback-state",
    )
    return token


def get_authed_client(token: str) -> Spotify:
    return Spotify(auth=token)


def get_best_cover_art_url(album: Dict[str, Any]) -> str:
    return sorted(
        album["images"], reverse=True, key=lambda img: img["height"] * img["width"]
    )[0]["url"]


def release_date_to_datetime(release_date: str) -> Optional[date]:
    parts = [int(p) for p in release_date.split("-")]
    if len(parts) == 3:
        return date(*parts)
    else:
        return None


def cover_art_cache(cover_art_url: str) -> str:
    """
    Saves the image to the cache, if it doesn't already exist.
    Returns the path.
    """
    cache_dir = path.expanduser("~/.cache/phelng/cover-arts")
    if not path.exists(cache_dir):
        makedirs(cache_dir)
    filename = get_cover_art_id(cover_art_url) + ".jpg"
    filepath = path.join(cache_dir, filename)
    if not path.exists(filepath):
        res = requests.get(cover_art_url, stream=True)
        with open(filepath, "wb") as file:
            copyfileobj(res.raw, file)

    return filepath


def get_cover_art_id(cover_art_url: str) -> str:
    return re.search(r"/image/([a-fA-F0-9]+)/?$", cover_art_url).group(1).lower()


class SpotifyClient:
    def __init__(self, client: Optional[Spotify] = None) -> None:
        self.c = client or Spotify(auth=get_spotify_token())

    def get_appropriate_track(self, track: Track) -> Optional[TrackSpotify]:
        results = self.c.search(self._build_search_query(track))["tracks"]["items"]
        if not len(results):
            return None
        # Filter for singles first, then albums, then compilations
        filter_by_album_type = lambda typ: [
            r for r in results if r["album"]["album_type"] == typ
        ]
        if len(filter_by_album_type("album")):
            selected = filter_by_album_type("album")[0]
        if len(filter_by_album_type("single")):
            selected = filter_by_album_type("single")[0]
        else:
            selected = results[0]

        return self.get_metadata(selected)

    @staticmethod
    def _build_search_query(track: Track) -> str:
        """
        Build a query with fields to request spotify with.
        See https://developer.spotify.com/documentation/web-api/reference/search/search/#writing-a-query
        """
        field = lambda name, value: f"{name.lower()}:{value.lower()} "
        query = field("artist", track.artist) + field("track", track.title)
        if track.album:
            query += field("album", track.album)
        return query

    def get_metadata(self, track: Dict[str, Any]) -> TrackSpotify:
        album = track["album"]
        # Handle case where the response includes a SimplifiedTrack object
        if "release_date" not in album or "tracks" not in album:
            album = self.c.album(track["album"]["id"])
        return TrackSpotify(
            artists=[a["name"] for a in track["artists"]],
            title=track["name"],
            album=album["name"],
            track_number=track["track_number"],
            duration=track["duration_ms"] / 1000,
            release_date=release_date_to_datetime(album["release_date"]),
            total_tracks=len(album["tracks"]),
            cover_art_url=get_best_cover_art_url(album),
        )

    def get_playlist(self, playlist_id: str) -> List[TrackSpotify]:
        results = self.c.playlist_tracks(playlist_id)
        return self._get_all_from_paginated(results)

    def _get_all_from_paginated(self, results) -> List[TrackSpotify]:
        tracks = results["items"]
        while results["next"]:
            results = self.c.next(results)
            tracks.extend(results["items"])
        tracks = [i["track"] for i in tracks if not i.get("is_local")]
        return [self.get_metadata(track) for track in tracks]

    def get_saved_tracks(self) -> List[TrackSpotify]:
        results = self.c.current_user_saved_tracks()
        return self._get_all_from_paginated(results)


def apply_metadata(
    filepath,
    metadata: Union[Track, TrackSpotify],
    try_to_convert=True,
    errors_hook=print,
):
    file = eyed3.load(filepath)
    if file.tag == None:
        file.initTag()

    file.tag.artist = file.tag.album_artist = metadata.artist
    file.tag.title = metadata.title
    if metadata.album:
        file.tag.album = metadata.album

    try:
        file.tag.track_num = metadata.track_number
        file.tag.track_total = metadata.total_tracks
        if metadata.release_date:
            file.tag.year = metadata.release_date.year
        file.tag.images.set(
            3, open(metadata.cover_art_filepath, "rb").read(), "image/png"
        )
    except AttributeError:
        pass

    file.tag.save()
