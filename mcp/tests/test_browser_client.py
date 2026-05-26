import httpx
import pytest
import respx

from browser_client.client import BrowserServiceClient
from registry.exceptions import BrowserServiceError


@pytest.mark.asyncio
@respx.mock
async def test_browser_client_calls_action_endpoint() -> None:
    route = respx.post("http://browser-service:8080/browser/action").mock(
        return_value=httpx.Response(200, json={"success": True, "data": {"text": "ok"}})
    )
    client = BrowserServiceClient(base_url="http://browser-service:8080", timeout_seconds=5)  # type: ignore[arg-type]
    result = await client.execute_action("session-1", "extract_text", {}, correlation_id="c1")
    await client.aclose()
    assert route.called
    assert result.success is True


@pytest.mark.asyncio
@respx.mock
async def test_browser_client_invalid_response() -> None:
    respx.post("http://browser-service:8080/browser/action").mock(
        return_value=httpx.Response(200, json={"unexpected": True})
    )
    client = BrowserServiceClient(base_url="http://browser-service:8080", timeout_seconds=5)  # type: ignore[arg-type]
    with pytest.raises(BrowserServiceError):
        await client.execute_action("session-1", "extract_text", {})
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_browser_client_calls_search_endpoint() -> None:
    route = respx.post("http://browser-service:8080/browser/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "results": [{"title": "MacBook", "url": "https://amazon.com"}],
                "observation": {"page_title": "Amazon MacBook Air"},
            },
        )
    )
    client = BrowserServiceClient(base_url="http://browser-service:8080", timeout_seconds=5)  # type: ignore[arg-type]
    result = await client.execute_search("session-1", "MacBook Air", correlation_id="c2")
    await client.aclose()
    assert route.called
    assert result.success is True
    assert result.data["page_title"] == "Amazon MacBook Air"
    assert result.data["search_results"] == [{"title": "MacBook", "url": "https://amazon.com"}]

