"""Strongly typed browser tool payloads (session_id is injected at execution time)."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class OpenUrlPayload(BaseModel):
    url: str
    tab_id: str | None = None


class ClickElementPayload(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    tab_id: str | None = None


class TypeTextPayload(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    text: str
    clear_first: bool = True
    tab_id: str | None = None


class ExtractTextPayload(BaseModel):
    target_ref: str | None = Field(
        default=None,
        description="Optional opaque reference from a semantic observation.",
    )
    tab_id: str | None = None


class ScreenshotPayload(BaseModel):
    full_page: bool = False
    tab_id: str | None = None


class GetDomSnapshotPayload(BaseModel):
    include_text: bool = True
    tab_id: str | None = None


class WaitForElementPayload(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    timeout_ms: int = Field(default=5000, ge=100, le=120_000)
    tab_id: str | None = None


class ScrollPagePayload(BaseModel):
    direction: Literal["up", "down"] = "down"
    amount_px: int = Field(default=800, ge=1, le=8000)
    tab_id: str | None = None


class GoBackPayload(BaseModel):
    tab_id: str | None = None


class HoverElementPayload(BaseModel):
    target_ref: str = Field(description="Opaque reference from a semantic observation.")
    tab_id: str | None = None


class PressKeyPayload(BaseModel):
    key: str = Field(description="Keyboard key name, e.g. Enter, Tab.")
    modifiers: list[str] = Field(default_factory=list)
    tab_id: str | None = None

    @field_validator("modifiers", mode="before")
    @classmethod
    def normalize_modifiers(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        raise TypeError("modifiers must be a list of strings")


class SelectDropdownPayload(BaseModel):
    target_ref: str
    value: str | None = None
    label: str | None = None
    tab_id: str | None = None


class UploadFilePayload(BaseModel):
    target_ref: str
    file_path: str = Field(description="Path or artifact id understood by the browser service.")
    tab_id: str | None = None


class SwitchTabPayload(BaseModel):
    tab_id: str = Field(description="Target tab identifier to activate.")


class CloseTabPayload(BaseModel):
    tab_id: str | None = Field(
        default=None,
        description="Tab to close; omit to close active tab per browser service policy.",
    )


class RefreshPagePayload(BaseModel):
    tab_id: str | None = None
    hard: bool = False


class GetPageMetadataPayload(BaseModel):
    tab_id: str | None = None


class ExtractLinksPayload(BaseModel):
    max_links: int = Field(default=100, ge=1, le=2000)
    tab_id: str | None = None


class ExtractTablesPayload(BaseModel):
    max_tables: int = Field(default=20, ge=1, le=200)
    tab_id: str | None = None


class ExecuteJavaScriptPayload(BaseModel):
    script: str = Field(max_length=16_384)
    tab_id: str | None = None

    @field_validator("script")
    @classmethod
    def no_null_bytes(cls, v: str) -> str:
        if "\x00" in v:
            raise ValueError("script must not contain null bytes")
        return v
