from __future__ import annotations

from typing import Any, Protocol

from schemas.api import CapabilitiesResponse, ToolCallRequest, ToolCallResponse, ToolListResponse
from schemas.responses import ToolResult


class McpTransport(Protocol):
    """Transport abstraction for exposing MCP tool operations."""

    async def list_tools(self) -> ToolListResponse: ...

    async def list_schemas(self) -> list[dict[str, Any]]: ...

    async def get_capabilities(self) -> CapabilitiesResponse: ...

    async def call_tool(self, request: ToolCallRequest) -> ToolCallResponse: ...


class ToolServiceBackend(Protocol):
    """Backend contract implemented by the MCP server runtime."""

    def list_tools(self) -> ToolListResponse: ...

    def list_schemas(self) -> list[dict[str, Any]]: ...

    def get_capabilities(self) -> CapabilitiesResponse: ...

    async def execute_tool(self, request: ToolCallRequest) -> ToolResult: ...
