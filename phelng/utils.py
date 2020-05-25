from typing import *
import os, sys
from shutil import get_terminal_size

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
