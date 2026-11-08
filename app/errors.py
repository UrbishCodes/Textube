from fastapi import Request
from fastapi.responses import JSONResponse

from youtube_transcript_api import (
    AgeRestricted,
    IpBlocked,
    NoTranscriptFound,
    NotTranslatable,
    RequestBlocked,
    TranscriptsDisabled,
    TranslationLanguageNotAvailable,
    VideoUnavailable,
)

from .services.video_id import InvalidVideoInput


def error_details(error: Exception) -> tuple[str, str, bool]:
    mappings = [
        (InvalidVideoInput, "INVALID_VIDEO_ID", "Enter a valid YouTube video URL or ID.", False),
        (TranscriptsDisabled, "TRANSCRIPTS_DISABLED", "This video does not have accessible transcripts.", False),
        (NoTranscriptFound, "NO_TRANSCRIPT_FOUND", "No matching transcript was found.", False),
        (VideoUnavailable, "VIDEO_UNAVAILABLE", "This video is unavailable.", False),
        (AgeRestricted, "AGE_RESTRICTED", "This video is age restricted.", False),
        (IpBlocked, "IP_BLOCKED", "YouTube blocked this request from the current IP address.", True),
        (RequestBlocked, "REQUEST_BLOCKED", "YouTube blocked this request. Try again later.", True),
        (NotTranslatable, "TRANSLATION_UNAVAILABLE", "This transcript cannot be translated.", False),
        (TranslationLanguageNotAvailable, "TRANSLATION_LANGUAGE_UNAVAILABLE", "That translation language is unavailable.", False),
        (LookupError, "TRACK_NOT_FOUND", "The selected transcript track is unavailable.", False),
    ]
    for exception_type, code, message, retryable in mappings:
        if isinstance(error, exception_type):
            return code, message, retryable
    return "TRANSCRIPT_REQUEST_FAILED", "Unable to retrieve the transcript. Please try again.", True


async def handle_app_error(request: Request, error: Exception) -> JSONResponse:
    code, message, retryable = error_details(error)
    status = 400 if code == "INVALID_VIDEO_ID" else 502
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "retryable": retryable}},
    )
