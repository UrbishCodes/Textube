from types import SimpleNamespace

from app.services.transcript_service import Track, TranscriptService, prefer_track


def test_prefer_track_order():
    tracks = [
        Track("German", "de", True, False, []),
        Track("English", "en", True, False, []),
        Track("English", "en", False, False, []),
    ]
    assert prefer_track(tracks) == tracks[2]


def test_fetch_only_selected_track(monkeypatch):
    fetched = []

    class Selected:
        language = "English"
        language_code = "en"
        is_generated = False

        def fetch(self, preserve_formatting):
            fetched.append(preserve_formatting)
            class Fetched:
                language = "English"
                language_code = "en"
                is_generated = False

                def __iter__(self):
                    return iter([])

            return Fetched()

    class Other(Selected):
        language_code = "de"

    class FakeApi:
        def list(self, video_id):
            return [Other(), Selected()]

    monkeypatch.setattr("app.services.transcript_service.YouTubeTranscriptApi", FakeApi)
    service = TranscriptService()
    result = service.fetch("dQw4w9WgXcQ", "en", "manual", True)
    assert result.language_code == "en"
    assert fetched == [True]
