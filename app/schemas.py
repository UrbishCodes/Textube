from typing import Literal

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    input: str = Field(min_length=1, max_length=2048)


class ParseResponse(BaseModel):
    video_id: str
    canonical_url: str


class TrackResponse(BaseModel):
    language: str
    language_code: str
    is_generated: bool
    is_translatable: bool
    translation_languages: list[dict[str, str]]


class TrackListRequest(BaseModel):
    video_id: str = Field(min_length=11, max_length=11)


class TrackListResponse(BaseModel):
    video_id: str
    tracks: list[TrackResponse]


class FetchRequest(TrackListRequest):
    language_code: str = Field(min_length=2, max_length=20)
    track_type: Literal["manual", "generated"]
    preserve_formatting: bool = True


class SegmentResponse(BaseModel):
    id: int
    text: str
    start: float
    duration: float
    end: float


class TranscriptResponse(BaseModel):
    video_id: str
    language: str
    language_code: str
    is_generated: bool
    segments: list[SegmentResponse]


class TranslateRequest(FetchRequest):
    target_language_code: str = Field(min_length=2, max_length=20)


class ErrorResponse(BaseModel):
    error: dict[str, str | bool]
