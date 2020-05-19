"""
Batch-download music with metadata from Spotify & audio from YouTube, using a .tsv file

Features:
	• Tries its best to download the correct audio from YouTube:
		— Checks if spotify's track duration and the YouTube video's match
		  (within --duration-check-margin seconds)
		— Prefers videos uploaded by "<artist>" or "<artist> - Topic"
		— If the track has multiple artists, (,-separated), first try all of them,
		  then try them one by one.
		— Exclude videos which contains "full album" in the title
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
	phelng FILES...

Options:
	-p --parallel-downloads INTEGER  Download up to INTEGER tracks in parallel
	--slugify-filenames              Save the filenames in a URL-compatible manner, 
	                                 separating track title and artist with a double dash "--"
	--keep-one-artist                Strip additionnal artist names from the "artists" field
	-N --network-limit NUMBER        Limit network usage (upload and download) by NUMBER kbps.

Actions (combinable):
If no actions are provided, `-dtn` is assumed.
	-d --download   Downloads mp3s
	-t --tag        Applies metadata to existing files
	-n --normalize  Normalizes the volume of existing files
"""
from typing import *
import docopt
import os
import sys
from pprint import pprint
from wcwidth import wcswidth
from shutil import get_terminal_size
from phelng.metadata import SpotifyClient, Track

def run(**args):
	args = args or docopt.docopt(__doc__)
	files = args['FILES']
	check_all_files_exist(files)
	library = merge_tsv_files(files)
	library = parse_tsv_lines(library)
	show_library(library, max_cell_width=40)
	
def check_all_files_exist(files: List[str]) -> bool:
	for file in files:
		if not os.path.exists(file):
			print(f"File {file!r} not found")
			sys.exit(1)
	return True
	
def merge_tsv_files(files: List[str]) -> Set[tuple]:
	"""
	Merges filepaths `files` and removes duplicate lines
	"""
	contents: Set[tuple] = set()
	for file in files:
		for line in open(file).read().split('\n'):
			# Ignore comments
			if line.startswith('# '): continue
			# Ignore empty lines
			if not line: continue
			if line in contents:
				print(f'warn: {line!r} appears more than once, ignoring duplicates.')
			contents.add(line)
	return contents
	
def parse_tsv_lines(lines: Set[str]) -> Set[Track]:
	parsed = set()
	for line in lines:
		cells = line.split('\t')
		if len(cells) == 2:
			cells = [cells[0], cells[1], None]
		if len(cells) != 3:
			print(f"error at line {line!r}: rows must have between 2 and 3 values (found {len(cells)})")
			sys.exit(1)
		
		artist, title, album = cells
		parsed.add(Track(artist=artist, title=title, album=album))
	return parsed

def show_library(library: Set[Track], max_cell_width: Optional[int] = None, padding = 2):
	max_cell_width = max_cell_width or terminal_width() - padding
	columns_lengths = {
		'artist': min(max((wcswidth(t.artist) for t in library)), max_cell_width) + padding,
		'title': min(max((wcswidth(t.title) for t in library)), max_cell_width) + padding,
		'album': min(max((wcswidth(t.album or '') for t in library)), max_cell_width),
	}
	header = Track(artist="ARTIST", title="TITLE", album="ALBUM")
	_print_row(header, columns_lengths)
	for row in library:
		track = SpotifyClient().get_appropriate_track(row) or row
		_print_row(track, columns_lengths)
def _add_cell_padding(cell:str, column_length:int) -> str:
	missing_spaces = column_length - wcswidth(cell)
	if missing_spaces < 0:
		cell = cell[:(column_length-1)] + '…'
	return cell + ' ' * missing_spaces

def _print_row(track: Track, columns_lengths: Dict[str, int]):
	row = \
		_add_cell_padding(track.artist, columns_lengths['artist']) \
		+ _add_cell_padding(track.title, columns_lengths['title']) \
		+ _add_cell_padding(track.album or '(Unknown)', columns_lengths['album'])
	print(row)
	
def terminal_width() -> int:
	return get_terminal_size((80, 80)).columns

if __name__ == "__main__":
	run(FILES=['.library-merged.tsv'])
