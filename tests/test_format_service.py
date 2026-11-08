import json

from app.services.format_service import FormatOptions, format_transcript
from app.services.transcript_service import Segment, Transcript


def transcript():
    return Transcript(
        video_id="dQw4w9WgXcQ",
        language="English",
        language_code="en",
        is_generated=False,
        segments=[
            Segment(0, "Hello, \"world\"", 0, 0, 0),
            Segment(1, "Next line", 1.5, 1, 2.5),
        ],
    )


def test_srt_uses_safe_end_for_zero_duration():
    output = format_transcript(transcript(), "srt", FormatOptions())
    assert "00:00:00,000 --> 00:00:01,500" in output
    assert "1\n" in output


def test_vtt_header_and_timestamp_separator():
    output = format_transcript(transcript(), "vtt", FormatOptions())
    assert output.startswith("WEBVTT\n\n")
    assert "00:00:01.500 --> 00:00:02.500" in output


def test_json_is_raw_api_compatible():
    output = json.loads(format_transcript(transcript(), "json", FormatOptions()))
    assert output == [
        {"text": 'Hello, "world"', "start": 0, "duration": 0},
        {"text": "Next line", "start": 1.5, "duration": 1},
    ]


def test_csv_quotes_text():
    output = format_transcript(transcript(), "csv", FormatOptions())
    assert '"Hello, ""world"""' in output


def test_empty_segments_are_removed_without_mutating_source():
    value = transcript()
    value.segments.append(Segment(2, "  ", 3, 1, 4))
    output = format_transcript(value, "plain", FormatOptions())
    assert "Next line" in output
    assert "  " not in output
    assert len(value.segments) == 3
