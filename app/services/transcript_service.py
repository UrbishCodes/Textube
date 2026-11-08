from dataclasses import dataclass
from typing import Iterable

from youtube_transcript_api import Transcript as LibraryTranscript
from youtube_transcript_api import TranscriptList, YouTubeTranscriptApi


@dataclass(frozen=True)
class Track:
    language: str
    language_code: str
    is_generated: bool
    is_translatable: bool
    translation_languages: list[dict[str, str]]


@dataclass(frozen=True)
class Segment:
    id: int
    text: str
    start: float
    duration: float
    end: float


@dataclass(frozen=True)
class Transcript:
    video_id: str
    language: str
    language_code: str
    is_generated: bool
    segments: list[Segment]


def _track_to_model(track: LibraryTranscript) -> Track:
    return Track(
        language=track.language,
        language_code=track.language_code,
        is_generated=track.is_generated,
        is_translatable=track.is_translatable,
        translation_languages=[
            {"language": language.language, "language_code": language.language_code}
            for language in track.translation_languages
        ],
    )


def prefer_track(tracks: Iterable[Track]) -> Track | None:
    tracks = list(tracks)
    for predicate in (
        lambda track: not track.is_generated and track.language_code == "en",
        lambda track: track.is_generated and track.language_code == "en",
        lambda track: not track.is_generated,
        lambda track: track.is_generated,
    ):
        selected = next((track for track in tracks if predicate(track)), None)
        if selected is not None:
            return selected
    return None


class TranscriptService:
    def list_tracks(self, video_id: str) -> list[Track]:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        return [_track_to_model(track) for track in transcript_list]

    def fetch(
        self,
        video_id: str,
        language_code: str,
        track_type: str,
        preserve_formatting: bool,
    ) -> Transcript:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        selected = self._find_track(transcript_list, language_code, track_type)
        fetched = selected.fetch(preserve_formatting=preserve_formatting)
        segments = [
            Segment(
                id=index,
                text=snippet.text,
                start=float(snippet.start),
                duration=float(snippet.duration),
                end=float(snippet.start) + float(snippet.duration),
            )
            for index, snippet in enumerate(fetched)
        ]
        return Transcript(
            video_id=video_id,
            language=fetched.language,
            language_code=fetched.language_code,
            is_generated=fetched.is_generated,
            segments=segments,
        )

    def translate(
        self,
        video_id: str,
        language_code: str,
        track_type: str,
        target_language_code: str,
        preserve_formatting: bool,
    ) -> Transcript:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        selected = self._find_track(transcript_list, language_code, track_type)
        translated = selected.translate(target_language_code)
        fetched = translated.fetch(preserve_formatting=preserve_formatting)
        return Transcript(
            video_id=video_id,
            language=fetched.language,
            language_code=fetched.language_code,
            is_generated=fetched.is_generated,
            segments=[
                Segment(
                    id=index,
                    text=snippet.text,
                    start=float(snippet.start),
                    duration=float(snippet.duration),
                    end=float(snippet.start) + float(snippet.duration),
                )
                for index, snippet in enumerate(fetched)
            ],
        )

    @staticmethod
    def _find_track(
        transcript_list: TranscriptList,
        language_code: str,
        track_type: str,
    ) -> Transcript:
        for track in transcript_list:
            if (
                track.language_code == language_code
                and track.is_generated == (track_type == "generated")
            ):
                return track
        raise LookupError("The selected transcript track is no longer available.")
