from typing import *

class YoutubeVideo(NamedTuple):
    title: str
    url: str
    uploader_name: str
    uploader_subscribers: int
    views: int
    description: str
    duration: int # seconds
