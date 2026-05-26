from typing import Any

import httpx
import pytest
import respx

from app.services.mcp_client.client import McpClient, McpToolExecutor
from app.services.mcp_client.protocol import ToolExecutionContext


@pytest.mark.asyncio
@respx.mock
async def test_mcp_client_executes_tool() -> None:
    respx.get("http://mcp:9000/v1/tools/schemas").mock(
        return_value=httpx.Response(200, json={"schemas": []})
    )
    route = respx.post("http://mcp:9000/v1/tools/call").mock(
        return_value=httpx.Response(
            200,
            json={"result": {"success": True, "data": {"text": "ok"}, "error": None, "metadata": {}}},
        )
    )
    client = McpClient(base_url="http://mcp:9000", timeout_seconds=5)  # type: ignore[arg-type]
    await client.get_tool_schemas(refresh=True)
    result = await client.execute_tool("extract_text", {}, session_id="s1")
    await client.aclose()
    assert route.called
    assert result.success is True
    assert result.data["text"] == "ok"


@pytest.mark.asyncio
@respx.mock
async def test_mcp_tool_executor_adapter() -> None:
    respx.get("http://mcp:9000/v1/tools/schemas").mock(
        return_value=httpx.Response(
            200,
            json={"schemas": [{"type": "function", "function": {"name": "extract_text"}}]},
        )
    )
    respx.post("http://mcp:9000/v1/tools/call").mock(
        return_value=httpx.Response(
            200,
            json={"result": {"success": True, "data": {"text": "via executor"}, "error": None, "metadata": {}}},
        )
    )
    client = McpClient(base_url="http://mcp:9000", timeout_seconds=5)  # type: ignore[arg-type]
    await client.get_tool_schemas(refresh=True)
    executor = McpToolExecutor(client)
    result = await executor.execute(
        "extract_text",
        {},
        ToolExecutionContext(session_id="abc"),
    )
    await client.aclose()
    assert result.success is True
    assert executor.openai_schemas()[0]["function"]["name"] == "extract_text"
