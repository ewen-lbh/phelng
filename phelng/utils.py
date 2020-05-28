from os.path import expanduser
from typing import *
import os, sys
from shutil import get_terminal_size
from pastel import colorize

def create_missing_files(*files) -> None:
    for file in files:
        if not os.path.exists(file):
            with open(file, "w") as f:
                f.write("")
            print(f"info: Created non-existent file {file!r}")

def check_all_files_exist(files: List[str]) -> bool:
    for file in files:
        if not os.path.exists(file):
            print(f"File {file!r} not found")
            sys.exit(1)
    return True

def terminal_width() -> int:
    return get_terminal_size((80, 80)).columns

def make_filename_safe(o: str, substitute: str = '-', remove_whitespace: bool = True, character_sets: Optional[Tuple[str]] = None) -> str:
    """
    Removes unsafe characters from string
    
    character_sets: a tuple of strings corresponding to `os.name` ('nt' or 'posix')
                    defaults to: `os.name`
    """
    unsafe_chars = {
        'posix': {'&', '$', ':', '?', '|', '`', ''},
        'nt': {'\\', '/', ':', '*', '?', '"', '<', '>', '|'},
    }
    absolutely_unsafe = {'\0', '\n', '/'}
    whitespace = {'\n', '\t', ' '}
    character_sets = character_sets if character_sets is not None else (os.name,)
    
    to_remove = absolutely_unsafe
    for character_set in character_sets:
        to_remove |= unsafe_chars[character_set]
    if remove_whitespace:
        to_remove |= whitespace
    
    safe = str()
    for c in o:
        if c in to_remove:
            c = substitute
        safe += c
    
    return safe
   
      

cache_dir = expanduser('~/.cache/phelng')

def cprint(msg: str) -> None:
    print(
        colorize(
            msg.replace("<b>", "<options=bold>")
            .replace("</b>", "</options=bold>")
            .replace("<red>", "<fg=red>")
            .replace("</red>", "</fg=red>")
            .replace("<green>", "<fg=green>")
            .replace("</green>", "</fg=green>")
            .replace("<dim>", "<options=dark>")
            .replace("</dim>", "</options=dark>")
        )
    )
