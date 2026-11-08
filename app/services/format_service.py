import csv
import io
import json
import re
from dataclasses import dataclass

from .transcript_service import Segment, Transcript


@dataclass(frozen=True)
class FormatOptions:
    timestamps: bool = False
    milliseconds: bool = False
    speakers: bool = False
    paragraph_grouping: bool = False
    trim: bool = True
    remove_empty: bool = True
    metadata: bool = False
    json_indent: int | None = 2


def timestamp(seconds: float, milliseconds: bool = False, separator: str = ":") -> str:
    total_ms = max(0, round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_value, millis = divmod(remainder, 1000)
    suffix = f".{millis:03d}" if milliseconds else ""
    return f"{hours:02d}{separator}{minutes:02d}{separator}{seconds_value:02d}{suffix}"


def _safe_segments(transcript: Transcript, options: FormatOptions) -> list[Segment]:
    result = []
    for segment in transcript.segments:
        text = segment.text.strip() if options.trim else segment.text
        if options.remove_empty and not text:
            continue
        result.append(Segment(segment.id, text, segment.start, segment.duration, segment.end))
    return result


def _text_lines(transcript: Transcript, options: FormatOptions) -> list[str]:
    lines = []
    for segment in _safe_segments(transcript, options):
        text = segment.text
        if options.speakers:
            speaker = getattr(segment, "speaker_id", None)
            if speaker:
                text = f"{speaker}: {text}"
        prefix = (
            f"[{timestamp(segment.start, options.milliseconds)}] "
            if options.timestamps
            else ""
        )
        lines.append(prefix + text)
    return lines


def _cue_end(segments: list[Segment], index: int) -> float:
    segment = segments[index]
    proposed = segment.end
    if proposed > segment.start:
        return proposed
    if index + 1 < len(segments) and segments[index + 1].start > segment.start:
        return segments[index + 1].start
    return segment.start + 0.1


def format_transcript(transcript: Transcript, format_name: str, options: FormatOptions) -> str:
    segments = _safe_segments(transcript, options)
    if format_name in {"plain", "timestamped", "speaker"}:
        lines = _text_lines(transcript, options)
        if options.paragraph_grouping:
            return " ".join(lines)
        return "\n".join(lines)
    if format_name in {"srt", "vtt"}:
        cues = []
        for index, segment in enumerate(segments):
            start = timestamp(segment.start, True, ":" if format_name == "srt" else ":")
            end = timestamp(_cue_end(segments, index), True, ":")
            if format_name == "srt":
                start, end = start.replace(".", ","), end.replace(".", ",")
                cues.append(f"{index + 1}\n{start} --> {end}\n{segment.text}")
            else:
                cues.append(f"{start} --> {end}\n{segment.text}")
        return ("WEBVTT\n\n" if format_name == "vtt" else "") + "\n\n".join(cues) + "\n"
    if format_name == "json":
        raw = [
            {"text": segment.text, "start": segment.start, "duration": segment.duration}
            for segment in segments
        ]
        return json.dumps(raw, ensure_ascii=False, indent=options.json_indent)
    if format_name == "json-enriched":
        return json.dumps(
            {
                "video_id": transcript.video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "segments": [
                    {
                        "id": segment.id,
                        "text": segment.text,
                        "start": segment.start,
                        "duration": segment.duration,
                        "end": segment.end,
                        "speaker_id": None,
                    }
                    for segment in segments
                ],
            },
            ensure_ascii=False,
            indent=options.json_indent,
        )
    if format_name == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["index", "start", "duration", "end", "speaker", "text"])
        for index, segment in enumerate(segments, 1):
            writer.writerow([index, segment.start, segment.duration, segment.end, "", segment.text])
        return output.getvalue()
    if format_name == "markdown":
        lines = []
        if options.metadata:
            lines.extend(
                [
                    "# Transcript",
                    "",
                    f"Source: https://www.youtube.com/watch?v={transcript.video_id}",
                    f"Language: {transcript.language}",
                    "",
                ]
            )
        lines.extend(
            f"- **{timestamp(segment.start, options.milliseconds)}** — {segment.text}"
            if options.timestamps or options.metadata
            else f"- {segment.text}"
            for segment in segments
        )
        return "\n".join(lines) + "\n"
    raise ValueError(f"Unsupported format: {format_name}")
