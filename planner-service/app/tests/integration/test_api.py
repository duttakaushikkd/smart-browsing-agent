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


def test_missing_session_status_returns_404(client: TestClient) -> None:
    response = client.get("/agent/missing/status")

    assert response.status_code == 404
