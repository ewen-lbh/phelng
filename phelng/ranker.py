from os import path
from typing import *
from phelng.youtube import YoutubeVideo, search
from phelng.metadata import Track, TrackSpotify, SpotifyClient
from phelng.utils import cprint
import re

def parse_trusted_channels_file(contents: str) -> List[str]:
    channels: List[str] = []
    for line in contents.split('\n'):
        channel = str()
        for c in line:
            channel += c
            if c == '(':
                break
        channels.append(channel.strip())
    return channels

class Ranker:
    def __init__(self, args: Dict[str, Any], track: Union[Track, TrackSpotify]) -> None:
        self.duration_exclude_margin = float(args["--duration-exclude-margin"])
        self.track = track
        with open(path.join(path.dirname(__file__), 'trusted_channels')) as file:
            self.trusted_channels = parse_trusted_channels_file(file.read())

    def duration(self, video: YoutubeVideo) -> bool:
        """
        Checks whether the given video is within --duration-check-margin
        """
        # Get the absolute difference between the youtube video and the spotify metadata
        duration_diff = abs(self.track.duration - video.duration)
        # Check if this duration is <= --duration-check-margin
        ret = duration_diff <= self.duration_exclude_margin
        cprint(f'    <dim>https://youtube.com/watch?v={video.video_id}</dim> duration check: <b><{"green" if ret else "red"}>{ret}</>  {self.track.duration}s -> {video.duration}s')
        return ret

    def uploader_name(self, video: YoutubeVideo) -> bool:
        """
        Gives a score based on the uploader name
        """
        # When the uploader matches the artist, it's better!
        if hasattr(self.track, "artists"):
            artists = self.track.artists
        else:
            artists = [self.track.artist]
        # Auto-generated YouTube artist channels tend to be named <artist> - Topic
        ret = any((artist.lower() == video.uploader_name.replace(' - Topic', '').lower() for artist in artists))
        if hasattr(self.track, 'label'):
            ret = ret or self.track.label.lower() == video.uploader_name.lower()
        cprint(f'    <dim>https://youtube.com/watch?v={video.video_id}</dim> uploader_name check: <b><{"green" if ret else "red"}>{ret}</>  {artists} -> {video.uploader_name}')
        return ret

    def title(self, video: YoutubeVideo) -> bool:
        """
        Checks if the video title contains the track's
        (will be fuzzy-matching in the future)
        """
        words = self.track.title.split(' ')
        words = [w.lower().strip() for w in words]
        symbols = '-()' # Used by tracks on spotify to separate feat./remix statements from actual title.
        words = [w for w in words if w not in symbols]
        ret = any(( w for w in words if w in video.title.lower() ))
        cprint(f'    <dim>https://youtube.com/watch?v={video.video_id}</dim> title check: <b><{"green" if ret else "red"}>{ret}</>  {words} -> {video.title!r}')
        return ret

    def select(self, videos: List[YoutubeVideo]) -> Optional[YoutubeVideo]:
        """
        Selects the YouTube video to serve as the audio source
        by ranking the given videos
        """

        # Exclude videos that don't contain the title
        videos = [v for v in videos if self.title(v)]

        # If the video's artist matches the track's (or the label of the track's album), take that one immediately
        for video in videos:
            if self.uploader_name(video):
                return video

        # Exclude videos that don't match the duration threshold
        if hasattr(self.track, "duration"):
            videos = [v for v in videos if self.duration(v)]

        if len(videos) == 0:
            return None

        return videos[0]


if __name__ == "__main__":
    track = Track("Geotic", "Swiss Bicycle")
    videos = search(f"{track.artist} - {track.title}")
    import json

    open("temp.json", "w").write(json.dumps([v._asdict() for v in videos]))
    ranker = Ranker(
        {"--duration-exclude-margin": 5},
        SpotifyClient().get_appropriate_track(track) or track,
    )
    open("selected.json", "w").write(json.dumps(ranker.select(videos)._asdict()))
