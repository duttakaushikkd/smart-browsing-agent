from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_agent_returns_session_id(client: TestClient) -> None:
    response = client.post("/agent/start", json={"goal": "https://example.com"})

    assert response.status_code == 202
    body = response.json()
    assert body["session_id"]
    assert body["state"] == "planning"


def test_agent_start_allows_browser_cors_preflight(client: TestClient) -> None:
    response = client.options(
        "/agent/start",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_missing_session_status_returns_404(client: TestClient) -> None:
    response = client.get("/agent/missing/status")

    assert response.status_code == 404


def test_agent_stream_websocket_accepts_connection(client: TestClient) -> None:
    with client.websocket_connect("/agent/test-session/stream") as websocket:
        message = websocket.receive_json()

    assert message["event"] == "planner_update"
    assert message["message"] == "Stream connected"
    assert message["session_id"] == "test-session"
