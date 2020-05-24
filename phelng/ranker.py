from typing import *
from phelng.youtube import YoutubeVideo
from phelng.metadata import Track, TrackSpotify
import re


class Ranker:
    def __init__(self, args: Dict[str, Any], track: Union[Track, TrackSpotify]) -> None:
        self.duration_check_margin = args["--duration-check-margin"]
        self.duration_exclude_margin = args["--duration-exclude-margin"]
        self.track = track

    def duration(self, video: YoutubeVideo) -> int:
        """
        Checks whether the given video is within --duration-check-margin
        Returns:
            1 - Durations match
            0 - Durations don't match - only use this video as a fallback
            -1 - Exclude this video
        """
        # Get the absolute difference between the youtube video and the spotify metadata
        duration_diff = abs(self.track.duration - video.duration)
        # Check if this duration is <= --duration-check-margin
        if duration_diff <= self.duration_check_margin:
            return 1
        # Check if this duration is <= --duration-exclude-margin
        if duration_diff <= self.duration_exclude_margin:
            return 0
        # Exclude
        return -1

    def uploader_name(self, video: YoutubeVideo) -> int:
        """
        Gives a score based on the uploader name
        """
        # When the uploader matches the artist, it's better!
        if any((artist == video.uploader_name for artist in self.track.artists)):
            return 3
        # Auto-generated YouTube artist channels tend to be named <artist> - Topic
        if any(
            (
                f"{artist} - Topic" == video.uploader_name
                for artist in self.track.artists
            )
        ):
            return 2
        # Fallback case, score is 1
        return 1
    
    def is_full_album(self, video: YoutubeVideo) -> bool:
        """
        Checks if the video title contains "Full Album".
        If the track's album, title or artist contains "Full Album",
        always return `False`
        """
        if not any(
            (
                # do ._asdict.get because track.album could be undefined
                "full album" in self.track._asdict().get(f, "").lower()
                for f in ["album", "title", "artist"]
            )
        ):
            return re.match(r"full album", video.title) != None
        return False

    def select(self, videos: List[YoutubeVideo]) -> YoutubeVideo:
        """
        Selects the YouTube video to serve as the audio source
        by ranking the given videos
        """
        # Exclude videos that don't match the duration threshold
        if hasattr(self.track, "duration"):
            videos = [v for v in videos if self.duration(v) != -1]

        # Exlude videos that include "Full Album" in the title
        # (except if album/artist/track names are "Full Album")
        videos = [v for v in videos if not self.is_full_album(v)]

        # If the video's artist matches the track's, take that one immediately
        youtube_artist_extract_pattern = re.compile(r"(.+)(?: [-–] Topic)?")
        for video in videos:
            if (
                youtube_artist_extract_pattern.search(video.title).group(1)
                == self.track.artist
            ):
                return video
        
        return videos[0]
