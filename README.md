# Textube

Textube is a fast, local-first YouTube transcript workspace. Paste a YouTube
link or video ID, choose an available caption track, preview the transcript,
add optional manual speaker labels, and export it without sending transcript
content to a hosted service.

**Live demo:** [youtube-transcript-gui.vercel.app](https://youtube-transcript-gui.vercel.app)

The original `youtube-transcript-api` package remains the extraction engine.
Textube adds a small FastAPI service and a lightweight Svelte interface around
its public API.

## Features

- Local web app bound to `127.0.0.1`
- YouTube watch, short, Shorts, embed, and bare video ID input
- Manual and auto-generated transcript track selection
- Plain text, timestamped text, speaker-labeled text, SRT, WebVTT, JSON, CSV,
  and Markdown export
- Optional manual speaker annotations
- Copy to clipboard and predictable downloads
- No accounts, analytics, persistent transcript history, or third-party fonts
- Existing Python library API and tests preserved

## Requirements

- Python 3.8–3.15
- Node.js 18+ and npm for frontend development
- Poetry

## Quick start

Install the Python dependencies:

```bash
poetry install
```

Build the frontend:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start Textube:

```bash
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Free deployment

Textube is configured for Vercel. The production deployment builds the
frontend and serves the FastAPI API through a Python serverless function.

```bash
npx vercel deploy --prod
```

The project is deployed at
[youtube-transcript-gui.vercel.app](https://youtube-transcript-gui.vercel.app).
Vercel's free tier may apply usage limits and deployment protection.

## Frontend development

Run the backend in one terminal:

```bash
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run Vite in another:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` requests to the local backend.

## Testing

Run the application tests:

```bash
poetry run pytest tests
```

Run the complete application and upstream library suite:

```bash
poetry run pytest tests youtube_transcript_api/test
```

Check and build the frontend:

```bash
cd frontend
npm run check
npm run build
```

## API

The local service exposes:

- `GET /api/health`
- `POST /api/video/parse`
- `POST /api/transcripts/list`
- `POST /api/transcripts/fetch`
- `POST /api/transcripts/translate`

The API validates video references server-side, fetches only the selected
track, and returns safe structured errors without tracebacks or request
credentials.

## Project layout

```text
app/
  main.py                 FastAPI application
  schemas.py              Request and response models
  errors.py               Safe error mapping
  services/
    video_id.py           YouTube reference parsing
    transcript_service.py Library integration
    format_service.py     Export formatting
frontend/
  src/App.svelte          Textube interface
tests/                    Application tests
youtube_transcript_api/   Original extraction library
```

## Privacy and limitations

Textube runs locally, but transcript retrieval still requires requests to
YouTube. YouTube may rate-limit or block requests depending on the video and
network. Textube does not store cookies, credentials, transcript history, or
analytics data.

Speaker labels are manual annotations. The underlying caption API does not
provide speaker diarization, so Textube never presents speaker identities as
automatically detected.

## License

Textube retains the MIT license of the underlying project. See
[LICENSE](LICENSE).

## Fork attribution

Textube is a fork and extension of
[jdepoix/youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api).
Thank you to Jonas Depoix and the original contributors for the transcript
extraction library, its documentation, and the MIT-licensed foundation this
project builds on.
