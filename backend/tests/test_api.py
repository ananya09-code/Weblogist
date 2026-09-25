from fastapi.testclient import TestClient

from backend.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_scheme_is_rejected():
    response = TestClient(app).post("/api/v1/scans", json={"url": "file:///etc/passwd"})
    assert response.status_code == 422
