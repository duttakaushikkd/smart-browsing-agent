from typing import Any

from pydantic import BaseModel, Field

from app.schemas.tools import ToolResult


class ToolExecutionContext(BaseModel):
    """Planner-side execution context passed to remote MCP tools."""

    session_id: str
    correlation_id: str | None = None


class McpToolMetadata(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)


class McpToolListResponse(BaseModel):
    tools: list[McpToolMetadata]


class McpToolCallRequest(BaseModel):
    session_id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class McpToolCallResponse(BaseModel):
    result: ToolResult
    correlation_id: str | None = None
