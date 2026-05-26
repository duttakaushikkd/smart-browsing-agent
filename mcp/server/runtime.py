from __future__ import annotations

from typing import Any

from executors.engine import ToolExecutorEngine
from observability.tracing import trace_span
from registry.base import ToolExecutionContext
from registry.registry import ToolRegistry
from schemas.api import (
    CapabilitiesResponse,
    ToolCallRequest,
    ToolListResponse,
)
from schemas.responses import ToolResult
from transport.base import ToolServiceBackend


class McpToolService(ToolServiceBackend):
    """MCP server runtime bridging transport requests to tool execution."""

    def __init__(self, registry: ToolRegistry, executor: ToolExecutorEngine) -> None:
        self._registry = registry
        self._executor = executor

    def list_tools(self) -> ToolListResponse:
        return ToolListResponse(tools=self._registry.list_metadata())

    def list_schemas(self) -> list[dict[str, Any]]:
        return self._registry.openai_schemas()

    def get_capabilities(self) -> CapabilitiesResponse:
        return CapabilitiesResponse(tool_count=len(self._registry.names()))

    async def execute_tool(self, request: ToolCallRequest) -> ToolResult:
        context = ToolExecutionContext(
            session_id=request.session_id,
            correlation_id=request.correlation_id,
        )
        async with trace_span(
            "mcp_tool_call",
            tool=request.tool_name,
            session_id=request.session_id,
            correlation_id=request.correlation_id,
        ):
            return await self._executor.execute(
                name=request.tool_name,
                arguments=request.arguments,
                context=context,
            )
