from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from executors.engine import ToolExecutorEngine
from observability.middleware import CorrelationIdMiddleware
from registry.base import BaseTool, ToolExecutionContext
from registry.registry import ToolRegistry
from schemas.responses import ToolResult
from server.runtime import McpToolService
from transport.http import create_http_router


class ExtractTextTool(BaseTool[Any]):
    name = "extract_text"
    description = "extract"
    input_schema = type("Empty", (), {"model_validate": staticmethod(lambda _: object())})

    async def execute(self, context: ToolExecutionContext, payload: Any) -> ToolResult:
        del payload
        return ToolResult(success=True, data={"text": "hello", "session": context.session_id})


@pytest.fixture
def integration_client() -> Iterator[TestClient]:
    registry = ToolRegistry([ExtractTextTool()])
    executor = ToolExecutorEngine(registry=registry, timeout_seconds=5, max_retries=0)
    service = McpToolService(registry=registry, executor=executor)
    app = FastAPI()
    app.state.tool_service = service
    app.add_middleware(CorrelationIdMiddleware)
    app.include_router(create_http_router(lambda request: request.app.state.tool_service))
    with TestClient(app) as client:
        yield client


def test_server_integration_call(integration_client: TestClient) -> None:
    response = integration_client.post(
        "/v1/tools/call",
        json={"session_id": "abc", "tool_name": "extract_text", "arguments": {}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["success"] is True
    assert body["result"]["data"]["text"] == "hello"
