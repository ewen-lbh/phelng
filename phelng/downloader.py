from os import path
from typing import *
from phelng.utils import cache_dir, terminal_width
from phelng.metadata import Track
from youtube_dl import YoutubeDL
import sys
from pastel import colorize
from math import floor


class Downloader:
    def __init__(self) -> None:
        pass

    def download(self, youtube_url: str, save_as: str) -> None:
        """
        Downloads and returns the downloaded path
        """
        self.progress_bar = ProgressBar(0, length=80, filled='█', empty=colorize('<options=dark>▒</>'))
        donwloader = YoutubeDL(
            {
                "quiet": True,
                "progress_hooks": [lambda p: self.progress_hook(p)],
                "outtmpl": save_as,
                "format": "best/bestaudio",
                "cachedir": path.join(cache_dir, "download"),
                "noplaylist": True,
                "fixup": "warn",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": 'mp3',
                        "preferredquality": '5',
                        "nopostoverwrites": False
                    }
                ],
            }
        )
        donwloader.download([youtube_url])
        print("")

    def progress_hook(self, d: dict):
        if d["status"] == "downloading":
            estimation = False
            progress_unknown = False
            total_bytes = None
            if d.get("total_bytes"):
                total_bytes = d["total_bytes"]
            elif d.get("total_bytes_estimate"):
                total_bytes = d["total_bytes_estimate"]
                estimation = True
            else:
                progress_unknown = True

            if progress_unknown:
                self.progress_bar.left_text = "Downloading:   ...%▕"
                self.progress_bar.value = 0
                self.progress_bar.total = 1
            else:
                self.progress_bar.left_text = colorize(
                    f'<options=bold>Downloading:</> {d["downloaded_bytes"]/total_bytes*100:5.1f}%▕'
                )
                self.progress_bar.total = int(total_bytes or 0)
                self.progress_bar.value = int(d["downloaded_bytes"])
                if d.get("eta"):
                    minutes, seconds = divmod(d["eta"], 60)
                    self.progress_bar.right_text = f"▏ {minutes}'{seconds}\" remaining"
                else:
                    self.progress_bar.right_text = f"▏"
            self.progress_bar.display()
        elif d["status"] == "completed":
            print("Downloading: Done.")


class ProgressBar:
    def __init__(
        self,
        total: int,
        length: int = 80,
        value: int = 0,
        left_text: str = "]",
        right_text: str = "]",
        empty: str = " ",
        filled: str = "#",
    ) -> None:
        self.total = total
        self.length = length
        self.left_text = left_text
        self.right_text = right_text
        self.empty = empty
        self.filled = filled
        self.value = value

    def step(self, amount: int):
        self.value += amount
        if self.value > self.total:
            raise ValueError(
                f"The total value {self.value!r} is greater than the total {self.total!r}"
            )

    def display(self):
        left_text = self.left_text
        right_text = self.right_text
        # Make sure the progress bar doesn't exceed the terminal width
        bar_length = (
            min(terminal_width(), self.length) - len(left_text) - len(right_text)
        )
        filled_cells = int(self.value / self.total * bar_length)
        empty_cells = bar_length - filled_cells
        # print(self.value, '|', self.total, ':', self.value // self.total)

        sys.stdout.write("\r")
        sys.stdout.write(
            left_text
            + self.filled * filled_cells
            + self.empty * empty_cells
            + right_text
        )
        sys.stdout.flush()


if __name__ == "__main__":
    Downloader().download(
        input("Download YouTube video at URL "), input("and save the file at ")
    )
