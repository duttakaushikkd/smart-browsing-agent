from typing import Any

import pytest
from fastapi.testclient import TestClient

from registry.registry import ToolRegistry
from schemas.api import CapabilitiesResponse, ToolCallRequest, ToolListResponse
from schemas.responses import ToolResult
from server.runtime import McpToolService
from transport.http import create_http_router


class FakeExecutor:
    def openai_schemas(self) -> list[dict[str, Any]]:
        return [{"type": "function", "function": {"name": "extract_text"}}]

    async def execute(self, name: str, arguments: dict[str, Any], context: Any) -> ToolResult:
        del name, arguments, context
        return ToolResult(success=True, data={"text": "ok"})


class FakeRegistry:
    def list_metadata(self) -> list[Any]:
        from schemas.api import ToolMetadata

        return [ToolMetadata(name="extract_text", description="d", input_schema={})]

    def openai_schemas(self) -> list[dict[str, Any]]:
        return FakeExecutor().openai_schemas()

    def names(self) -> list[str]:
        return ["extract_text"]


@pytest.fixture
def client() -> TestClient:
    from fastapi import FastAPI

    app = FastAPI()
    service = McpToolService(registry=FakeRegistry(), executor=FakeExecutor())  # type: ignore[arg-type]
    app.state.tool_service = service
    app.include_router(create_http_router(lambda request: request.app.state.tool_service))
    return TestClient(app)


def test_http_list_tools(client: TestClient) -> None:
    response = client.get("/v1/tools")
    assert response.status_code == 200
    payload = ToolListResponse.model_validate(response.json())
    assert payload.tools[0].name == "extract_text"


def test_http_call_tool(client: TestClient) -> None:
    response = client.post(
        "/v1/tools/call",
        json=ToolCallRequest(session_id="s1", tool_name="extract_text", arguments={}).model_dump(),
    )
    assert response.status_code == 200
    assert response.json()["result"]["success"] is True


def test_http_capabilities(client: TestClient) -> None:
    response = client.get("/v1/capabilities")
    assert response.status_code == 200
    payload = CapabilitiesResponse.model_validate(response.json())
    assert payload.tool_count == 1
