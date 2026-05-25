from typing import Any

import pytest

from app.core.config import Settings
from app.core.security import UrlPolicy
from app.planner.tools import ToolExecutionContext, ToolRegistry, create_browser_api_tools
from app.schemas.tools import ToolResult


class FakeBrowserServiceClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def execute_action(
        self,
        session_id: str,
        action: str,
        payload: dict[str, Any],
    ) -> ToolResult:
        self.calls.append((session_id, action, payload))
        return ToolResult(success=True, data={"text": "ok"}, metadata={"latency_ms": 1})


@pytest.mark.asyncio
async def test_tool_registry_validates_and_dispatches_browser_tool() -> None:
    client = FakeBrowserServiceClient()
    registry = ToolRegistry(
        create_browser_api_tools(
            client,  # type: ignore[arg-type]
            UrlPolicy(Settings(allowed_domains=["example.com"], blocked_domains=[])),
        )
    )

    result = await registry.execute(
        "open_url",
        {"url": "https://example.com"},
        ToolExecutionContext(session_id="abc"),
    )

    assert result.success is True
    assert client.calls == [("abc", "open_url", {"url": "https://example.com"})]


@pytest.mark.asyncio
async def test_tool_registry_returns_schema_for_openai_tools() -> None:
    client = FakeBrowserServiceClient()
    registry = ToolRegistry(
        create_browser_api_tools(
            client,  # type: ignore[arg-type]
            UrlPolicy(Settings(allowed_domains=[], blocked_domains=[])),
        )
    )

    schemas = registry.openai_schemas()

    assert {schema["function"]["name"] for schema in schemas} >= {"open_url", "click_element"}
