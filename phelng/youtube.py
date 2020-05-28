from typing import *
import urllib.parse
import json
from bs4 import BeautifulSoup
import requests
import re


class YoutubeVideo(NamedTuple):
    title: str
    url: str
    uploader_name: str
    # uploader_subscribers: int (impossible without an API call)
    views: int
    description: str
    duration: int  # seconds
    video_id: str
    is_verified_artist: bool


def parse_results_html(results_html: str) -> List[YoutubeVideo]:
    results = []
    viewcount_extract_pattern = re.compile(r"[^\d]*([\d ]+)[^\d]*")
    soup = BeautifulSoup(results_html, "html.parser")
    for result in soup.select(".yt-uix-tile"):
        result_url = result.select_one(".yt-uix-tile-link")["href"]
        if result_url.startswith("/watch?v=") and result.select_one(".video-time") is not None:
            try:
                duration_strs = result.select_one(".video-time").string.split(":")
                duration_int = 60 * int(duration_strs[0]) + int(duration_strs[1])
                description_element = result.select_one(".yt-lockup-description")
                description = description_element.text if description_element is not None else ''
                video_info = YoutubeVideo(
                    video_id=result_url[result_url.index("=") + 1 :],
                    title=result.select_one(".yt-uix-tile-link")["title"],
                    description=description,
                    duration=duration_int,
                    uploader_name=result.select_one(".yt-lockup-byline a").string,
                    url="https://youtube.com" + result_url,
                    views=int(
                        viewcount_extract_pattern.search(
                            result.select_one(".yt-lockup-meta-info").text
                        ).group(1)
                    ),
                    is_verified_artist=result.select_one('.yt-channel-title-icon-verified') is not None
                )
                results.append(video_info)
            except Exception as e:
                print(f'{result!r}')
                print(e)
    return results


def get_results_html(query: str) -> str:
    encoded_search = urllib.parse.quote(query)
    url = f"https://youtube.com/results?search_query={encoded_search}&pbj=1"
    return requests.get(url).text


def search(query: str) -> List[YoutubeVideo]:
    results = get_results_html(query)
    with open('temp.html', 'w') as f:
        f.write(results)
    videos = parse_results_html(results)
    return videos
