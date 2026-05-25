from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OpenUrlArgs(BaseModel):
    url: str
    tab_id: str | None = None


class ClickElementArgs(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    tab_id: str | None = None


class TypeTextArgs(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    text: str
    clear_first: bool = True
    tab_id: str | None = None


class ExtractTextArgs(BaseModel):
    target_ref: str | None = Field(
        default=None,
        description="Optional opaque reference from a semantic observation.",
    )
    tab_id: str | None = None


class ScreenshotArgs(BaseModel):
    full_page: bool = False
    tab_id: str | None = None


class WaitForElementArgs(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    tab_id: str | None = None


class DomSnapshotArgs(BaseModel):
    include_text: bool = True
    tab_id: str | None = None


class ScrollPageArgs(BaseModel):
    direction: Literal["up", "down"] = "down"
    amount_px: int = Field(default=800, ge=1, le=5000)
    tab_id: str | None = None


class GoBackArgs(BaseModel):
    tab_id: str | None = None
