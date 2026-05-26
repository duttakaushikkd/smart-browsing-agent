from typing import Any

from pydantic import BaseModel, Field

from schemas.responses import ToolResult


class ToolCallRequest(BaseModel):
    """MCP-compatible remote tool invocation request."""

    session_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class ToolCallResponse(BaseModel):
    result: ToolResult
    correlation_id: str | None = None


class ToolMetadata(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class ToolListResponse(BaseModel):
    tools: list[ToolMetadata]


class ToolSchemasResponse(BaseModel):
    schemas: list[dict[str, Any]]


class CapabilitiesResponse(BaseModel):
    protocol_version: str = "1.0"
    transports: list[str] = Field(default_factory=lambda: ["http"])
    tool_count: int
    supports_discovery: bool = True
