from urllib.parse import parse_qs, urlparse
import re


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class InvalidVideoInput(ValueError):
    """Raised when input is not a supported YouTube video reference."""


def parse_video_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise InvalidVideoInput("Enter a YouTube URL or video ID.")
    if VIDEO_ID_PATTERN.fullmatch(value):
        return value

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        raise InvalidVideoInput("Enter a valid YouTube video URL or 11-character video ID.")

    host = parsed.hostname.lower().rstrip(".")
    path_parts = [part for part in parsed.path.split("/") if part]
    video_id: str | None = None
    if host in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        if path_parts and path_parts[0] in {"shorts", "embed"} and len(path_parts) > 1:
            video_id = path_parts[1]
        else:
            video_id = parse_qs(parsed.query).get("v", [None])[0]
    elif host == "youtu.be" and path_parts:
        video_id = path_parts[0]

    if video_id is None or not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise InvalidVideoInput("Enter a valid YouTube video URL or 11-character video ID.")
    return video_id


def canonical_url(video_id: str) -> str:
    if not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise InvalidVideoInput("Invalid YouTube video ID.")
    return f"https://www.youtube.com/watch?v={video_id}"
