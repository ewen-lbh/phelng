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
    -p --parallel-downloads INTEGER    Download up to INTEGER tracks in parallel
    --slugify-filenames                Save the filenames in a URL-compatible manner, 
                                       separating track title and artist with a double dash "--"
    --keep-one-artist                  Strip additionnal artist names from the "artists" field
    -N --network-limit NUMBER          Limit network usage (upload and download) by NUMBER kbps.
    --duration-exclude-margin NUMBER   Videos that are more than ±this seconds long 
                                       than the track will not be selected for download [default: 5]

Actions (combinable, executed in the presented order):
If no actions are provided, `-dtn` is assumed.
    -a --add-to       Adds the tracks from one of your spotify playlists to FILE
    -l --list         Show the library
    -d --download     Downloads mp3s
    -n --normalize    Normalizes the volume of existing files
    -t --tag          Applies metadata to existing FILE
"""
from os import rename
from os import path
from phelng.normalize import normalize_file
from phelng.youtube import search
from phelng.ranker import Ranker
from typing import *
import docopt
from wcwidth import wcswidth
from phelng.metadata import SpotifyClient, Track, TrackSpotify, apply_metadata
from phelng.downloader import Downloader
from phelng.utils import (
    cache_dir,
    create_missing_files,
    check_all_files_exist,
    make_filename_safe,
    terminal_width,
)
from phelng.library_files import (
    append_tracks_to_library,
    merge_tsv_files,
    parse_tsv_lines,
)
from PyInquirer import prompt, ValidationError, Validator
from pastel import colorize
import re


def cprint(msg: str) -> None:
    print(
        colorize(
            msg.replace("<b>", "<options=bold>")
            .replace("</b>", "</options=bold>")
            .replace("<red>", "<fg=red>")
            .replace("</red>", "</fg=red>")
            .replace("<dim>", "<options=dark>")
            .replace("</dim>", "</options=dark>")
        )
    )


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
    library = list(library)

    if args["--list"]:
        show_library(library)
    if args["--download"] or args["--tag"]:
        spotify = SpotifyClient()
    if args["--download"]:
        for track in library:
            print("\n")
            cprint(f"{track.artist} <dim>—</dim> <b>{track.title}</b>{ ' <dim>[</dim>' + track.album + '<dim>]</dim>' if track.album else ''}")
            # cprint(
            #     f"<b>Track:</b>       <dim>artist:</dim>{track.artist} <dim>title:</dim>{track.title} <dim>album:</dim>{track.album}"
            # )
            cprint(
                f"<b>Spotify:</b>     <dim>Searching for</dim> {spotify._build_search_query(track)}"
            )
            metadata = spotify.get_appropriate_track(track)
            if metadata:
                cprint(
                    f"<b>Metadata:</b>    <dim>artist:</dim>{metadata.artist} <dim>title:</dim>{metadata.title} <dim>album:</dim>{metadata.album}"
                )
                cprint(
                    f"             <dim>track_number:</dim>{metadata.track_number} <dim>duration:</dim>{metadata.duration}s <dim>release_date:</dim>{metadata.release_date and metadata.release_date.isoformat()}"
                )
                cprint(
                    f"             <dim>total_tracks:</dim>{metadata.total_tracks} <dim>cover_art_url:</dim>{metadata.cover_art_url}"
                )
            else:
                metadata = track
                cprint(f"<b>Spotify:</b>\n  <red>Error:     No search results</red>")

            # Get YouTube video URL to download
            ranker = Ranker(args, metadata)
            query = f"{metadata.artist} - {metadata.title}" + (
                f" {track.album}" if track.album else ""
            )
            cprint(f"<b>YouTube:</b>     <dim>Searching for </dim>{query}")
            videos = search(query)
            if not len(videos):
                cprint(f"  <red>Error:       No results found.</red>")
                continue
            video = ranker.select(videos)
            if video is None:
                cprint(
                    f"<b>YouTube:</b>     <red>No videos that satisfy filtering conditions. Try to adjust settings like <b>--duration-exclude-margin</b></red>"
                )
                continue
            cprint(
                f"<b>Selected:</b>    {video.title} <dim>by</dim> {video.uploader_name}\n             <dim>at</dim> {video.url}"
            )
            filename = (
                make_filename_safe(
                    f"{metadata.artist}--{metadata.title}"
                    + (f"--{metadata.album}" if track.album else "")
                )
                + ".mp3"
            )
            cprint(f"<b>Saving as:</b>   {filename.replace('.mp3', colorize('<options=dark>.mp3</>'))}")
            try:
                Downloader().download(
                    video.url, save_as=filename.replace(".mp3", ".%(ext)s")
                )
            except Exception:
                cprint(f"<red>  Error:     Error while downloading with youtube-dl</red>")
            if args["--tag"]:
                cprint(f"<b>Tags:</b>        <dim>Applying to</dim> {filename}")
                apply_metadata(
                    filename,
                    track,
                    errors_hook=lambda msg: print(f"  Error:     {msg}"),
                )
            if args["--normalize"]:
                cprint(f"<b>Normalize:</b>   {filename} <dim>to</dim> 20 <dim>dBFS</dim>")
                filepath_temp = path.join(cache_dir, "normalize", filename)
                try:
                    normalize_file(filename, filepath_temp)
                    rename(filepath_temp, filename)
                except Exception as e:
                    cprint(
                        f"<red><b>  Error:</b>     Couldn't normalize {filename}</red>"
                    )


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
