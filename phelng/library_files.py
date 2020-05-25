from typing import *
from phelng.metadata import Track, TrackSpotify

def merge_tsv_files(files: List[str]) -> Set[tuple]:
    """
	Merges filepaths `files` and removes duplicate lines
	"""
    contents: Set[tuple] = set()
    for file in files:
        for line in open(file).read().split("\n"):
            # Ignore comments
            if line.startswith("\t"):
                continue
            # Ignore empty lines
            if not line:
                continue
            if line in contents:
                print(f"warn: {line!r} appears more than once, ignoring duplicates.")
            contents.add(line)
    return contents


def parse_tsv_lines(lines: Set[str]) -> Set[Track]:
    parsed = set()
    for line in lines:
        cells = line.split("\t")
        if len(cells) == 2:
            cells = [cells[0], cells[1], None]
        if len(cells) != 3:
            print(
                f"error at line {line!r}: rows must have between 2 and 3 values (found {len(cells)})"
            )
            sys.exit(1)

        artist, title, album = cells
        parsed.add(Track(artist=artist, title=title, album=album))
    return parsed

def append_tracks_to_library(tracks: List[TrackSpotify], append_to: str) -> None:
    with open(append_to, "a") as file:
        file.write("\n".join((t.to_tsv() for t in tracks)) + "\n")
