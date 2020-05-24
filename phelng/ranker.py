from typing import *
from phelng.youtube import YoutubeVideo, search
from phelng.metadata import Track, TrackSpotify, SpotifyClient
import re


class Ranker:
    def __init__(self, args: Dict[str, Any], track: Union[Track, TrackSpotify]) -> None:
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
        return duration_diff <= self.duration_exclude_margin

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

    def select(self, videos: List[YoutubeVideo]) -> YoutubeVideo:
        """
        Selects the YouTube video to serve as the audio source
        by ranking the given videos
        """
        # Exclude videos that don't match the duration threshold
        if hasattr(self.track, "duration"):
            videos = [v for v in videos if self.duration(v)]

        # If the video's artist matches the track's, take that one immediately
        youtube_artist_extract_pattern = re.compile(r"(.+)(?: [-–] Topic)?")
        for video in videos:
            if (
                youtube_artist_extract_pattern.search(video.title).group(1)
                == self.track.artist
            ):
                return video

        return videos[0]


if __name__ == "__main__":
    track = Track("Geotic", "Swiss Bicycle")
    videos = search(f"{track.artist} - {track.title}")
    import json
    open("temp.json", "w").write(json.dumps([ v._asdict() for v in videos ]))
    ranker = Ranker(
        {"--duration-exclude-margin": 5},
        SpotifyClient().get_appropriate_track(track) or track,
    )
    open("selected.json", "w").write(json.dumps(ranker.select(videos)._asdict()))

