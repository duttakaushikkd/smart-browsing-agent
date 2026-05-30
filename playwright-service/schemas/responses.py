from typing import Any
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Normalized browser execution result payload."""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionCreateResponse(BaseModel):
    session_id: str


class SessionCloseRequest(BaseModel):
    session_id: str


class SessionCloseResponse(BaseModel):
    success: bool


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    tabs: list[str] = Field(default_factory=list)
