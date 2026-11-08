from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .errors import handle_app_error
from .schemas import (
    FetchRequest,
    ParseRequest,
    ParseResponse,
    SegmentResponse,
    TrackListRequest,
    TrackListResponse,
    TrackResponse,
    TranslateRequest,
    TranscriptResponse,
)
from .services.transcript_service import TranscriptService
from .services.video_id import canonical_url, parse_video_id

app = FastAPI(title="Transcript", docs_url=None, redoc_url=None)
app.add_exception_handler(Exception, handle_app_error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["content-type"],
)

service = TranscriptService()
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "transcript"}


@app.post("/api/video/parse", response_model=ParseResponse)
def parse_video(request: ParseRequest) -> ParseResponse:
    video_id = parse_video_id(request.input)
    return ParseResponse(video_id=video_id, canonical_url=canonical_url(video_id))


@app.post("/api/transcripts/list", response_model=TrackListResponse)
def list_transcripts(request: TrackListRequest) -> TrackListResponse:
    video_id = parse_video_id(request.video_id)
    tracks = service.list_tracks(video_id)
    return TrackListResponse(
        video_id=video_id,
        tracks=[TrackResponse.model_validate(track, from_attributes=True) for track in tracks],
    )


def _transcript_response(transcript) -> TranscriptResponse:
    return TranscriptResponse(
        video_id=transcript.video_id,
        language=transcript.language,
        language_code=transcript.language_code,
        is_generated=transcript.is_generated,
        segments=[SegmentResponse.model_validate(segment, from_attributes=True) for segment in transcript.segments],
    )


@app.post("/api/transcripts/fetch", response_model=TranscriptResponse)
def fetch_transcript(request: FetchRequest) -> TranscriptResponse:
    video_id = parse_video_id(request.video_id)
    return _transcript_response(
        service.fetch(video_id, request.language_code, request.track_type, request.preserve_formatting)
    )


@app.post("/api/transcripts/translate", response_model=TranscriptResponse)
def translate_transcript(request: TranslateRequest) -> TranscriptResponse:
    video_id = parse_video_id(request.video_id)
    return _transcript_response(
        service.translate(
            video_id,
            request.language_code,
            request.track_type,
            request.target_language_code,
            request.preserve_formatting,
        )
    )


if frontend_dist.exists():
    @app.get("/{path:path}", include_in_schema=False)
    async def frontend(path: str) -> FileResponse:
        requested = frontend_dist / path
        if path and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_dist / "index.html")
