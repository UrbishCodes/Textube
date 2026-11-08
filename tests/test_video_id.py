import pytest

from app.services.video_id import InvalidVideoInput, canonical_url, parse_video_id


VIDEO_ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "value",
    [
        VIDEO_ID,
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
    ],
)
def test_parse_supported_video_references(value):
    assert parse_video_id(value) == VIDEO_ID


@pytest.mark.parametrize(
    "value",
    ["", "https://example.com/video", "https://youtube.com/playlist?list=abc", "too-short"],
)
def test_reject_invalid_video_references(value):
    with pytest.raises(InvalidVideoInput):
        parse_video_id(value)


def test_canonical_url():
    assert canonical_url(VIDEO_ID) == f"https://www.youtube.com/watch?v={VIDEO_ID}"
