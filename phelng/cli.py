"""
Batch-download music with metadata from Spotify & audio from YouTube, using a .tsv file

Features:
    • Tries its best to download the correct audio from YouTube:
        — Checks if spotify's track duration and the YouTube video's match
          (within --duration-check-margin seconds)
        — Prefers videos uploaded by "<artist>" or "<artist> - Topic"
        — If the track has multiple artists, (,-separated), first try all of them,
          then try them one by one.
    • Normalizes the audio
    • Downloads up to --parallel-downloads tracks at the same time
    • Applies as much IDv3 tags as possible, using Spotify's API:
        — Track title
        — Artist
        — Album
        — Release date
        — Cover art
    • The album is chosen wisely, with certain types of albums having greater priority:
        1. Albums
        2. EPs
        3. Singles
        4. Compilations
    • Slugifies the downloaded file's names (with --slugify-filenames)
    • Caches the cover art pictures to avoid downloading them multiple times
    • Provides options to throttle the network usage so you can use it in the background

Usage:
    phelng [-l] [-d] [-n] [-t] [options] FILE...
    phelng -a [-l] [-d] [-n] [-t] [options] FILE

Options:
    -p --parallel-downloads INTEGER  Download up to INTEGER tracks in parallel
    --slugify-filenames              Save the filenames in a URL-compatible manner, 
                                     separating track title and artist with a double dash "--"
    --keep-one-artist                Strip additionnal artist names from the "artists" field
    -N --network-limit NUMBER        Limit network usage (upload and download) by NUMBER kbps.

Actions (combinable, executed in the presented order):
If no actions are provided, `-dtn` is assumed.
    -a --add-to       Adds the tracks from one of your spotify playlists to FILE
    -l --list         Show the library
    -d --download     Downloads mp3s
    -n --normalize    Normalizes the volume of existing files
    -t --tag          Applies metadata to existing FILE
"""
from typing import *
import docopt
from wcwidth import wcswidth
from phelng.metadata import SpotifyClient, Track, TrackSpotify
from phelng.downloader import download_library
from phelng.utils import create_missing_files, check_all_files_exist, terminal_width
from phelng.library_files import append_tracks_to_library, merge_tsv_files, parse_tsv_lines
from PyInquirer import prompt, ValidationError, Validator
import re

def run():
    args = docopt.docopt(__doc__)
    files = args["FILE"]
    spotify = SpotifyClient()
    if args["--add-to"]:
        create_missing_files(*files)
        if len(files) != 1:
            print("Please specify exactly one file in the --add-to mode")
            exit(1)

        chosen_playlist = choose_playlist(spotify)
        append_tracks_to_library(chosen_playlist, append_to=files[0])
    check_all_files_exist(files)
    library = merge_tsv_files(files)
    library = parse_tsv_lines(library)
    
    if args["--list"]:
        show_library(library)
    if args["--download"]:
        download_library(library)
    
def show_library(library: Set[Track], max_cell_width: Optional[int] = None, padding=2):
    max_cell_width = max_cell_width or terminal_width() - padding
    columns_lengths = {
        "artist": min(max((wcswidth(t.artist) for t in library)), max_cell_width)
        + padding,
        "title": min(max((wcswidth(t.title) for t in library)), max_cell_width)
        + padding,
        "album": min(max((wcswidth(t.album or "") for t in library)), max_cell_width),
    }
    header = Track(artist="ARTIST", title="TITLE", album="ALBUM")
    _print_row(header, columns_lengths)
    for row in library:
        _print_row(row, columns_lengths)


def _add_cell_padding(cell: str, column_length: int) -> str:
    missing_spaces = column_length - wcswidth(cell)
    if missing_spaces < 0:
        cell = cell[: (column_length - 1)] + "…"
    return cell + " " * missing_spaces


def _print_row(track: Track, columns_lengths: Dict[str, int]):
    row = (
        _add_cell_padding(track.artist, columns_lengths["artist"])
        + _add_cell_padding(track.title, columns_lengths["title"])
        + _add_cell_padding(track.album or "(Unknown)", columns_lengths["album"])
    )
    print(row)


def choose_playlist(spotify: SpotifyClient) -> List[TrackSpotify]:
    playlist_input_method = prompt(
        [
            {
                "type": "list",
                "name": "ans",
                "message": "Choose a playlist by",
                "choices": [
                    "Inputting its ID",
                    "Selecting from your playlists",
                    "Using your saved tracks",
                ],
            }
        ]
    )["ans"]

    if playlist_input_method == "Selecting from your playlists":
        print("Fetching your playlists...", end="")
        sys.stdout.flush()
        playlists = spotify.c.current_user_playlists()["items"]
        print(" Done.")
        playlist_name = prompt(
            [
                {
                    "type": "list",
                    "name": "ans",
                    "message": "Add tracks from playlist",
                    "choices": playlists,
                }
            ]
        )["ans"]
        playlist_id = [p for p in playlists if p["name"] == playlist_name][0]["id"]
        print("Getting the playlist's tracks...", end="")
        sys.stdout.flush()
        playlist = spotify.get_playlist(playlist_id)
    elif playlist_input_method == "Using your saved tracks":
        print("Getting your saved tracks...", end="")
        sys.stdout.flush()
        playlist = spotify.get_saved_tracks()
    else:

        class SpotifyPlaylistIDValidator(Validator):
            def validate(self, document):
                ok = re.match(r"^[0-9A-Za-z_-]{22}$", document.text)
                if not ok:
                    raise ValidationError(
                        message="Please enter a valid spotify playlist ID",
                        cursor_position=len(document.text),
                    )  # Move cursor to end

        playlist_id = prompt(
            {
                "type": "input",
                "name": "ans",
                "message": "Enter the spotify playlist ID",
                "validate": SpotifyPlaylistIDValidator,
            }
        )["ans"]

        print("Getting the playlist's tracks...", end="")
        sys.stdout.flush()
        playlist = spotify.get_playlist(playlist_id)
    print(f" Done: got {len(playlist)} track(s)")
    return playlist


if __name__ == "__main__":
    run()
