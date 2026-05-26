from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Normalized tool response envelope."""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
