from typing import Any
from pydantic import BaseModel, Field


class BrowserActionRequest(BaseModel):
    session_id: str
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class BrowserSearchRequest(BaseModel):
    session_id: str
    query: str


class BrowserExtractRequest(BaseModel):
    session_id: str
    target_ref: str | None = None
    tab_id: str | None = None
