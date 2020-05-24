from phelng.metadata import Track, TrackSpotify, SpotifyClient
from typing import *
from youtube_dl import YoutubeDL

def download(youtube_url: str, save_as: Optional[str] = None) -> None:
    """
    Downloads and returns the downloaded path
    """
    donwloader = YoutubeDL()
    donwloader.download([youtube_url])

def download_track(track: Track):
    metadata = SpotifyClient().get_metadata(track._asdict())
    
    
def download_library(library: Set[Track]):
    pass
            

if __name__ == "__main__":
    download('https://youtube.com/watch?v=jBVKFjZooJk')
