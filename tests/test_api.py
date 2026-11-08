from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_parse_video():
    response = TestClient(app).post(
        "/api/video/parse", json={"input": "https://youtu.be/dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    assert response.json()["video_id"] == "dQw4w9WgXcQ"


def test_invalid_video_error_shape():
    response = TestClient(app, raise_server_exceptions=False).post(
        "/api/video/parse", json={"input": "https://example.com"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_VIDEO_ID"
