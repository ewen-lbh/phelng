"""
phelng - Batch-download music with metadata from Spotify & audio from YouTube, using a .tsv file

Usage:
	phelng FILES...
"""
from typing import *
import docopt
import os
import sys

def run():
	args = docopt.docopt(__doc__)
	check_all_files_exist(args['FILES'])
	
def check_all_files_exist(files: List[str]) -> bool:
	for file in files:
		if not os.path.exists(file):
			print(f"File {file!r} not found")
			sys.exit(1)
	return True
	
