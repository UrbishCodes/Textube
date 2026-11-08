# Build Specification --- YouTube Transcript GUI

**Repository:** https://github.com/UrbishCodes/youtube-transcript-gui\
**Document purpose:** Implementation-ready product and engineering
brief\
**Primary goal:** Turn the existing Python `youtube-transcript-api` fork
into a fast, minimal, local-first GUI for fetching, viewing, formatting,
editing, and exporting YouTube transcripts.

------------------------------------------------------------------------

## 1. Product direction

Build a **local web GUI** that runs on the user's computer and opens in
the browser. The Python repository remains the source of truth for
transcript extraction. Add a thin local application layer around it and
keep the frontend lightweight.

The product should feel like a focused utility, not a dashboard:

-   One obvious input: YouTube URL or video ID.
-   One primary action: **Get transcript**.
-   Fast transcript preview with no unnecessary navigation.
-   Format selection that updates the output immediately after the
    transcript has been fetched.
-   One-click copy and download.
-   Advanced options remain collapsed until needed.

Do not build a cloud service, account system, analytics dashboard, AI
summarizer, or Electron wrapper for the first version. Do not replace or
rewrite the transcript extraction library.

### Core interaction

1.  User pastes a YouTube URL or video ID.
2.  App validates and extracts the video ID.
3.  App discovers available transcript tracks.
4.  User chooses a language/track, or accepts the sensible default.
5.  App fetches the selected track once.
6.  Transcript appears in the preview.
7.  User switches output format and formatting options.
8.  Preview updates locally without another YouTube request.
9.  User copies the result or downloads it.

**Important performance principle:** Fetching is network-bound.
Formatting is local. Never refetch just because the user changes
TXT/SRT/VTT/JSON, timestamps, speaker labels, or display preferences.

------------------------------------------------------------------------

## 2. Repository audit and integration constraints

The target repository is a fork of `jdepoix/youtube-transcript-api`. The
inspected `master` branch contains the Python package and its tests, not
an existing GUI application.

Relevant existing files:

-   `youtube_transcript_api/_api.py` --- `YouTubeTranscriptApi`,
    `list(video_id)` and
    `fetch(video_id, languages=..., preserve_formatting=...)`.
-   `youtube_transcript_api/_transcripts.py` --- `TranscriptList`,
    `Transcript`, `FetchedTranscript`, and `FetchedTranscriptSnippet`.
-   `youtube_transcript_api/formatters.py` --- existing JSON,
    pretty-print, plain-text, WebVTT and SRT formatters.
-   `youtube_transcript_api/_errors.py` --- typed extraction errors.
-   `youtube_transcript_api/test/` --- existing tests and static YouTube
    response fixtures.
-   `pyproject.toml` --- Poetry project configuration and existing
    test/lint tasks.

The fork currently identifies itself as `youtube-transcript-api` version
`1.2.5`. Its existing package API exposes:

``` python
from youtube_transcript_api import YouTubeTranscriptApi

api = YouTubeTranscriptApi()
transcript_list = api.list(video_id)

for track in transcript_list:
    print(
        track.language,
        track.language_code,
        track.is_generated,
        track.is_translatable,
        track.translation_languages,
    )

fetched = track.fetch()
snippets = fetched.to_raw_data()
```

Each fetched snippet contains:

``` python
{
    "text": "A transcript segment",
    "start": 1.25,
    "duration": 2.40
}
```

The `FetchedTranscript` also exposes `video_id`, `language`,
`language_code`, `is_generated`, iteration, indexing, length, and
`to_raw_data()`.

### Integration rules

-   Use the public package API. Do not import private fetcher/parser
    internals from `_api.py` or `_transcripts.py`.
-   Create one `YouTubeTranscriptApi` instance per worker/request. The
    repository explicitly warns that the underlying `requests.Session`
    is not thread-safe.
-   Use `list(video_id)` for language and track discovery. Fetch the
    selected `Transcript` object only after selection.
-   Keep the fetched transcript object or a normalized immutable segment
    list in application state for the current job.
-   Reuse existing formatter classes where they meet the output
    requirements. Add application-specific formatters in a separate
    GUI/application module rather than modifying upstream formatters
    unnecessarily.
-   Preserve the existing library tests and add GUI/service tests
    separately.
-   Do not silently change the library's dependency versions, supported
    Python range, CLI behavior, or public API.
-   Review the current `pyproject.toml` before adding dependencies. Keep
    new GUI dependencies in clearly separated application dependencies
    if practical.

### Existing limitation to design around

The current snippet model has text, start time, and duration. It does
**not** provide speaker identities, word-level timestamps, confidence
scores, or true diarization. Speaker labels must therefore be an
explicit manual annotation feature. Never pretend the API detected
speakers automatically.

------------------------------------------------------------------------

## 3. Recommended architecture

Use a small local client/server architecture:

### Backend

-   Python 3.10+ recommended for the GUI application runtime; preserve
    the library's existing supported Python range unless a deliberate
    compatibility decision is made.
-   FastAPI for a small local HTTP API.
-   Uvicorn to serve the API and built frontend assets.
-   Existing `youtube-transcript-api` package for extraction.
-   Pydantic models for request/response validation.
-   Standard library `json`, `csv`, and `pathlib` for serialization and
    downloads.

The backend should bind to `127.0.0.1` only by default. Do not expose
the local app to the network.

### Frontend

Use **Svelte + TypeScript + Vite** for a small, responsive UI with
minimal runtime overhead.

-   No heavy component framework or large UI kit.
-   Use CSS variables and a small set of reusable components.
-   Use native browser text rendering and controls wherever possible.
-   Build static frontend assets and serve them from the Python app in
    production.
-   During development, run Vite and FastAPI separately with a
    configured local proxy.

If the repository's existing conventions make Svelte impractical, an
equivalent lightweight TypeScript frontend is acceptable. Do not
introduce React solely by habit.

### Suggested application structure

Add application code without moving the existing package:

``` text
youtube-transcript-gui/
├── youtube_transcript_api/       # Existing library; preserve
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app and static asset mounting
│   ├── schemas.py                # API request/response models
│   ├── services/
│   │   ├── transcript_service.py # Calls the existing Python API
│   │   ├── video_id.py           # URL parsing and validation
│   │   └── format_service.py     # Output serializers
│   └── errors.py                 # Safe error mapping
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── App.svelte
│   │   └── app.css
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   ├── test_video_id.py
│   ├── test_transcript_service.py
│   ├── test_format_service.py
│   └── test_api.py
├── build.md
└── README.md
```

This is a proposed structure, not a claim that these files already
exist. Adapt names to the actual repository after checking its current
state.

------------------------------------------------------------------------

## 4. User interface and visual direction

### Overall layout

A single-page application with a restrained visual hierarchy.

**Header** - Small product name/wordmark: `Transcript`. - Minimal status
indicator (Local / Ready). - Settings icon only if there are real
settings to expose.

**Input area** - Wide URL input with placeholder:
`Paste a YouTube link or video ID`. - Primary button:
`Get transcript`. - Enter key submits. - Paste should work naturally. -
Show a compact inline validation message rather than a modal.

**Video and track information** After a successful lookup, show: - Video
ID and a clickable YouTube video link. - Selected transcript language. -
Track type: Manual or Auto-generated. - Optional compact track selector
when multiple tracks are available. - A clear loading state while tracks
or transcript data are being fetched.

Do not scrape video thumbnails or metadata as a prerequisite for
transcript extraction. If a title is not available through a supported
source, do not invent one.

**Transcript workspace** - Main content area is a readable transcript
preview. - Format selector is visible above the preview. - Secondary
formatting options appear conditionally based on the selected format. -
Copy and Download actions are grouped at the top-right of the preview. -
Show segment count and approximate transcript duration in subdued
metadata. - Long transcripts must remain scrollable without making the
entire page excessively tall.

### Visual style

-   Minimal, neutral, typography-led.
-   Light theme first; dark theme is optional but should be easy to add.
-   One accent color for primary actions.
-   Thin borders, subtle separators, restrained radius.
-   No gradients, glassmorphism, oversized cards, animated backgrounds,
    or decorative charts.
-   Use a monospace font for raw/code-like output and a highly readable
    sans-serif for the application UI.
-   Keyboard focus states must be visible.
-   Responsive down to mobile widths.

### Interaction details

-   Disable the fetch button only while a request is active.
-   Show progress states: `Checking video`, `Finding transcripts`,
    `Fetching transcript`.
-   Do not show fake percentage progress for a request whose duration is
    unknown.
-   Preserve the current transcript if a later fetch attempt fails.
-   Switching formats must be immediate and must not display a loading
    spinner.
-   Copy action should show a short success/failure message.
-   Download filename should be predictable,
    e.g. `youtube_<video_id>_en.srt`.
-   Warn before discarding unsaved manual speaker annotations when
    loading another video.

------------------------------------------------------------------------

## 5. Transcript retrieval workflow

### URL parsing

Accept: - `https://www.youtube.com/watch?v=VIDEO_ID` -
`https://youtu.be/VIDEO_ID` -
`https://www.youtube.com/shorts/VIDEO_ID` -
`https://www.youtube.com/embed/VIDEO_ID` - A bare video ID.

Validate the extracted ID before calling the library. Do not accept
arbitrary URLs as video IDs. Reject playlist-only URLs unless a valid
video ID is also present. Do not fetch arbitrary user-supplied domains.

### Track discovery

Call:

``` python
transcript_list = YouTubeTranscriptApi().list(video_id)
```

Return a normalized list of available tracks with: - `language` -
`language_code` - `is_generated` - `is_translatable` - available
translation language codes/names where exposed

Default selection: 1. Prefer manually created English (`en`) if
available. 2. Otherwise prefer generated English (`en`) if available. 3.
Otherwise select the first available manual track. 4. If no manual track
exists, select the first generated track. 5. If there are no tracks,
show a useful error.

The user must be able to select a different available track. Do not
silently translate a transcript. Translation is an explicit user action.

### Fetch

Fetch only the selected track:

``` python
fetched = selected_track.fetch(preserve_formatting=True)
```

Preserve formatting in the source data where useful, but render it
safely in the UI. Never inject transcript HTML directly into the DOM.
Treat transcript text as untrusted text.

Store normalized segments:

``` typescript
type TranscriptSegment = {
  id: number;
  text: string;
  start: number;
  duration: number;
  end: number;
  speakerId?: string | null;
};
```

`end` is derived as `start + duration`. Retain the original start and
duration values. Do not mutate source timing data during text cleanup.

------------------------------------------------------------------------

## 6. Transcript formats

The format selector should expose these formats:

  -----------------------------------------------------------------------
  Format                  Extension               Purpose
  ----------------------- ----------------------- -----------------------
  Plain text              `.txt`                  Text only, no
                                                  timestamps

  Timestamped text        `.txt`                  Readable transcript
                                                  with timestamps

  Speaker-labeled text    `.txt`                  Transcript with
                                                  manually assigned
                                                  speaker labels

  SRT subtitles           `.srt`                  Widely supported
                                                  subtitle format

  WebVTT subtitles        `.vtt`                  Web subtitle/caption
                                                  format

  JSON                    `.json`                 Structured data with
                                                  text and timing

  CSV                     `.csv`                  Spreadsheet-friendly
                                                  segment data

  Markdown                `.md`                   Readable transcript
                                                  document
  -----------------------------------------------------------------------

### 6.1 Plain text

One segment per line or merged into readable paragraphs depending on the
selected text layout option.

Default:

``` text
This is the first sentence.
This is the next sentence.
```

No timestamps or speaker labels by default.

### 6.2 Timestamped text

Readable timestamp plus text:

``` text
[00:00:01] This is the first sentence.
[00:00:04] This is the next sentence.
```

Timestamp precision options: - `HH:MM:SS` - `HH:MM:SS.mmm`

Default: `HH:MM:SS`.

### 6.3 Speaker-labeled text

``` text
[00:00:01] Speaker 1: Welcome to the video.
[00:00:04] Speaker 2: Thanks for having me.
```

Rules: - Speaker labels are manual annotations, not inferred from the
API. - Provide an optional speaker assignment control for each
segment. - Allow renaming `Speaker 1`, `Speaker 2`, etc. to names. -
Allow consecutive segments assigned to the same speaker to be grouped in
readable output. - If no speaker is assigned, do not invent one. Either
omit the label or use an explicit `Unknown` setting chosen by the
user. - Preserve the original segment boundaries unless the user
explicitly enables grouping.

### 6.4 SRT

Use the existing `SRTFormatter` where appropriate, but add validation
and regression tests for edge cases.

Expected shape:

``` srt
1
00:00:01,000 --> 00:00:03,400
First subtitle line.

2
00:00:03,400 --> 00:00:06,000
Second subtitle line.
```

Requirements: - Sequential cue numbering beginning at 1. - Timestamp
separator is a comma before milliseconds. - Each cue has a start and end
time. - Blank line between cues. - UTF-8 output. - Ensure end time is
greater than start time. If source duration is zero or invalid, derive a
safe fallback from the next segment start or a small minimum cue
duration and make this behavior testable. - Preserve cue order by start
time. Do not silently reorder source segments without a deliberate
normalization step.

### 6.5 WebVTT

Use the existing `WebVTTFormatter` where appropriate.

Expected shape:

``` vtt
WEBVTT

00:00:01.000 --> 00:00:03.400
First subtitle line.

00:00:03.400 --> 00:00:06.000
Second subtitle line.
```

Requirements: - Must begin with `WEBVTT`. - Millisecond separator is a
period. - Cue timing uses `start --> end`. - UTF-8 output. - Escape or
sanitize cue payloads according to WebVTT rules. - If speaker labels are
enabled and supported, use valid WebVTT voice spans only when the
speaker identity is genuinely assigned. Otherwise export plain cue text.

### 6.6 JSON

Offer two explicit JSON choices:

**Raw API-compatible JSON**

``` json
[
  {
    "text": "Hello there",
    "start": 0.0,
    "duration": 1.54
  }
]
```

This should match `FetchedTranscript.to_raw_data()` and remain suitable
for scripts expecting the library's raw segment shape.

**Enriched JSON**

``` json
{
  "video_id": "VIDEO_ID",
  "language": "English",
  "language_code": "en",
  "is_generated": false,
  "segments": [
    {
      "id": 0,
      "text": "Hello there",
      "start": 0.0,
      "duration": 1.54,
      "end": 1.54,
      "speaker_id": null
    }
  ]
}
```

Use UTF-8, stable field names, valid JSON escaping, and optional
indentation (compact / pretty). Do not silently add metadata to the raw
API-compatible mode.

### 6.7 CSV

Columns:

``` csv
index,start,duration,end,speaker,text
1,0.0,1.54,1.54,,Hello there
```

Use Python's `csv` module, not manual string concatenation. Correctly
quote commas, quotes, and newlines. UTF-8 output. Include speaker only
as an empty field when no speaker is assigned.

### 6.8 Markdown

Readable document with optional title, video link, language, and
timestamps:

``` markdown
# Transcript

Source: https://www.youtube.com/watch?v=VIDEO_ID
Language: English

- **00:00:01** — First sentence.
- **00:00:04** — Second sentence.
```

Metadata header should be optional and removable.

------------------------------------------------------------------------

## 7. Formatting and cleanup controls

Keep cleanup conservative and reversible. The original fetched segments
must always remain available.

Suggested options:

-   Include timestamps: on/off.
-   Timestamp precision: seconds / milliseconds.
-   Include speaker labels: on/off.
-   Merge adjacent segments into paragraphs: on/off.
-   Remove empty/whitespace-only segments: on/off, default on.
-   Trim leading/trailing whitespace: on, default.
-   Preserve inline formatting tags: on/off, default off for plain text.
-   Add transcript metadata header: on/off.
-   JSON indentation: compact / 2 spaces / 4 spaces.
-   Text layout: one segment per line / paragraph grouping.

Do not: - Rewrite, paraphrase, summarize, or grammatically correct
transcript text automatically. - Remove repeated words just because they
look like ASR duplication. - merge segments in a way that loses their
timestamps. - claim that cleanup improves transcription accuracy. - use
an LLM for cleanup in the first version.

If paragraph grouping is enabled, retain the original segment data
internally and only combine text for the selected output. Use a
deterministic grouping rule, such as a configurable maximum gap between
segments. Make the threshold visible and conservative.

------------------------------------------------------------------------

## 8. API design

Keep the local API small.

### `POST /api/video/parse`

Request:

``` json
{ "input": "https://youtu.be/VIDEO_ID" }
```

Response:

``` json
{ "video_id": "VIDEO_ID", "canonical_url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```

### `POST /api/transcripts/list`

Request:

``` json
{ "video_id": "VIDEO_ID" }
```

Response:

``` json
{
  "video_id": "VIDEO_ID",
  "tracks": [
    {
      "language": "English",
      "language_code": "en",
      "is_generated": false,
      "is_translatable": true,
      "translation_languages": []
    }
  ]
}
```

### `POST /api/transcripts/fetch`

Request:

``` json
{
  "video_id": "VIDEO_ID",
  "language_code": "en",
  "track_type": "manual",
  "preserve_formatting": true
}
```

Response:

``` json
{
  "video_id": "VIDEO_ID",
  "language": "English",
  "language_code": "en",
  "is_generated": false,
  "segments": [
    { "id": 0, "text": "Hello", "start": 0.0, "duration": 1.5, "end": 1.5 }
  ]
}
```

The service must verify that the requested language and track type are
actually available. Do not accept a client-supplied arbitrary track URL.

### `POST /api/transcripts/translate`

Optional first-release feature. Request should include video ID, source
language, target language, and track type. Only expose it when the
selected track reports that translation is available and the library
supports the operation. Translation must be explicit and should be
fetched once like any other track.

### `GET /api/health`

Return a minimal local health response.

### Error response shape

``` json
{
  "error": {
    "code": "TRANSCRIPTS_DISABLED",
    "message": "This video does not have accessible transcripts.",
    "retryable": false
  }
}
```

Map known library exceptions into stable error codes. Do not expose
Python tracebacks, request headers, cookies, proxy credentials, or
internal server paths to the browser.

Potential errors include invalid video ID, video unavailable,
transcripts disabled, no matching transcript, IP blocked/request
blocked, age restricted, translation unavailable, and unexpected network
errors.

------------------------------------------------------------------------

## 9. Performance requirements

Treat these as measurable goals, not marketing claims.

-   Format switching after a transcript is loaded: under 50 ms for
    ordinary transcripts on a modern desktop.
-   Local UI interaction: no unnecessary network requests.
-   Initial UI should be small and render quickly.
-   Do not load a video player or thumbnail by default.
-   Do not fetch all languages' transcript bodies. Discover track
    metadata, then fetch only the selected track.
-   Do not perform formatting in the browser on every keystroke if the
    transcript is large; use memoized derived output.
-   Use a virtualized transcript list only if profiling shows it is
    necessary. Avoid adding virtualization complexity prematurely.
-   Keep a single normalized transcript state in memory.
-   Avoid serializing the entire transcript repeatedly between frontend
    and backend for format changes. Prefer client-side formatting from
    the already fetched segment data, or a single export request when a
    file is requested.
-   Add request cancellation or stale-response protection so an older
    fetch cannot overwrite a newer selection.
-   Keep the backend local and avoid external analytics, telemetry, and
    third-party scripts.

### Caching

For the first version, cache the current fetched transcript in memory
for the lifetime of the app session. Do not build a persistent database
unless the user asks for transcript history.

If adding a cache later: - Key by video ID + language code + track
type + translation target. - Never mix manual and generated tracks. -
Provide a clear way to clear cached data. - Do not cache failures as
successful empty transcripts.

------------------------------------------------------------------------

## 10. Security and privacy

-   Bind to `127.0.0.1`, not `0.0.0.0`.
-   Validate video IDs server-side.
-   Do not allow the backend to fetch arbitrary user-provided URLs.
-   Do not render transcript text as HTML.
-   Do not log full transcript content by default.
-   Do not store YouTube cookies or account credentials.
-   Do not add analytics or remote font/CDN dependencies.
-   Restrict CORS to the local development origin; production should
    serve frontend and API from the same origin.
-   Protect state-changing local endpoints against cross-origin requests
    where applicable.
-   Limit input length and enforce reasonable response/request sizes.
-   Make clear that YouTube may block or rate-limit requests. A GUI
    cannot guarantee successful extraction for every video or IP
    address.

------------------------------------------------------------------------

## 11. Testing plan

Keep existing upstream tests passing.

### Unit tests

-   YouTube URL parsing for watch, short, shorts, embed and bare IDs.
-   Invalid URLs and malformed IDs.
-   Track preference ordering.
-   Manual versus generated track selection.
-   Timestamp formatting at 0, fractional seconds, minute/hour
    boundaries and long videos.
-   SRT cue numbering and timestamp separator.
-   WebVTT header and timestamp separator.
-   JSON raw output matches `to_raw_data()`.
-   Enriched JSON metadata and speaker fields.
-   CSV quoting for commas, quotes, Unicode and embedded newlines.
-   Empty segment handling.
-   Zero/negative duration handling.
-   Speaker labels omitted when unassigned.
-   Paragraph grouping does not mutate source segments.

### Integration tests

-   Mock `YouTubeTranscriptApi.list()` and `Transcript.fetch()`.
-   Verify only the selected track is fetched.
-   Verify switching output format does not call the transcript API
    again.
-   Verify a failed new fetch does not erase the previous successful
    transcript.
-   Verify typed library exceptions map to safe API errors.
-   Verify concurrent requests do not share a `YouTubeTranscriptApi`
    instance.

### UI tests

-   Paste URL and submit with button/Enter.
-   Loading and disabled states.
-   Select language and track type.
-   Switch output format and see preview update.
-   Copy and download each supported format.
-   Speaker assignment and renaming.
-   Responsive layout.
-   Keyboard navigation and focus visibility.
-   Long transcript scrolling.

### Acceptance criteria

The first release is complete when:

1.  A user can paste a valid YouTube URL or video ID and fetch an
    available transcript.
2.  The app lists available languages and manual/generated tracks.
3.  The user can choose a track before fetching.
4.  The transcript appears in a readable preview.
5.  The user can switch between Plain text, Timestamped text,
    Speaker-labeled text, SRT, WebVTT, JSON, CSV and Markdown.
6.  Format switching does not trigger another extraction request.
7.  Raw JSON exactly preserves the API's `text`, `start`, and `duration`
    fields.
8.  Speaker labels are manual and never presented as automatic
    diarization.
9.  Copy and download work with Unicode text.
10. Errors are understandable and do not expose internal traces.
11. Existing package tests and new application tests pass.
12. The app starts locally with a documented command.

------------------------------------------------------------------------

## 12. Implementation phases

### Phase 1 --- Repository-safe foundation

-   Inspect current branch and working tree before editing.
-   Preserve the existing package and tests.
-   Add the application folder and dependencies.
-   Add video ID parsing and service layer.
-   Add FastAPI health endpoint.
-   Add mocked service tests.

**Deliverable:** Backend can parse a video ID, list tracks, and fetch
one selected transcript.

### Phase 2 --- Minimal GUI

-   Add Svelte + TypeScript + Vite.
-   Build the single-page input and transcript workspace.
-   Add loading, empty, success and error states.
-   Connect the UI to the local API.

**Deliverable:** User can fetch and view a transcript.

### Phase 3 --- Formatting and export

-   Implement the format selector.
-   Reuse existing formatters where correct.
-   Implement timestamped text, speaker-labeled text, CSV and Markdown.
-   Add copy/download.
-   Add deterministic cleanup and paragraph grouping options.

**Deliverable:** Every required format works without refetching.

### Phase 4 --- Speaker annotations and polish

-   Add manual per-segment speaker assignment.
-   Add speaker rename controls.
-   Add keyboard interactions and responsive layout.
-   Improve long-transcript performance based on profiling.

**Deliverable:** Polished, usable transcript editor.

### Phase 5 --- Packaging and documentation

-   Add one-command local startup.
-   Document installation, development, tests and troubleshooting.
-   Keep local-only security defaults.
-   Verify clean install from a fresh clone.

**Deliverable:** Reproducible local app setup.

------------------------------------------------------------------------

## 13. Developer commands and setup expectations

Exact commands should be finalized after checking the repository's
existing Poetry configuration and chosen frontend package manager.

Expected workflow:

``` bash
# Python dependencies
poetry install

# Frontend dependencies
cd frontend
npm install

# Frontend development server
npm run dev

# Backend development server (from repository root)
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Existing library tests
poetry run pytest youtube_transcript_api

# New application tests
poetry run pytest tests
```

Production mode should build the frontend and serve its static assets
through FastAPI so the user does not need to keep two development
servers running.

Add a simple cross-platform startup script or documented command after
the development flow is stable. Do not make the app dependent on Docker.

------------------------------------------------------------------------

## 14. Scope boundaries and non-goals

Do not include in the first release:

-   Automatic speaker diarization.
-   AI summarization, rewriting, translation outside the library's
    supported translation feature, or grammar correction.
-   Batch downloads, playlists, or channel-wide transcript extraction.
-   User accounts, cloud sync, databases, or hosted backend.
-   Video playback/editor features.
-   Browser extensions.
-   Electron/Tauri packaging before the local web app is stable.
-   Proxy purchasing or bundled proxy credentials.

These can be evaluated later without complicating the first working
release.

------------------------------------------------------------------------

## 15. Research references

The implementation should follow the actual repository API and the
subtitle format specifications:

-   Target fork: https://github.com/UrbishCodes/youtube-transcript-gui
-   Upstream project documentation:
    https://github.com/jdepoix/youtube-transcript-api
-   Upstream formatter implementation:
    https://github.com/jdepoix/youtube-transcript-api/blob/master/youtube_transcript_api/formatters.py
-   W3C WebVTT specification: https://www.w3.org/TR/webvtt1/
-   MDN WebVTT format guide:
    https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API/Web_Video_Text_Tracks_Format

WebVTT is a formal time-aligned caption format. SRT is also widely used
by subtitle tools. Keep their timestamp syntax distinct: SRT uses a
comma before milliseconds, while WebVTT uses a period.

------------------------------------------------------------------------

## Final implementation instruction

Build the smallest complete application that satisfies the acceptance
criteria. Prioritize extraction reliability, immediate local format
switching, correct subtitle serialization, and a clean interface.
Preserve the existing API library. Do not overengineer the app, add
features outside this specification, or claim speaker detection that the
underlying transcript data does not provide.
