from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlparse

from registry.exceptions import ToolValidationError
from security.url_policy import UrlPolicy

ALLOWED_ACTIONS = {
    "open_url",
    "click_element",
    "type_text",
    "extract_text",
    "screenshot",
    "get_dom_snapshot",
    "wait_for_element",
    "scroll_page",
    "go_back",
    "hover_element",
    "press_key",
    "select_dropdown",
    "upload_file",
    "switch_tab",
    "close_tab",
    "refresh_page",
    "get_page_metadata",
    "extract_links",
    "extract_tables",
    "execute_javascript",
}


def ensure_action_allowed(action: str) -> None:
    if action not in ALLOWED_ACTIONS:
        raise ToolValidationError(f"Action not allowed: {action}")


def sanitize_payload(payload: Mapping[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, str) and "\x00" in value:
            raise ToolValidationError(f"Field {key} contains null bytes")
        clean[key] = value
    return clean


def validate_session_id(session_id: str) -> None:
    if not session_id or len(session_id.strip()) < 3:
        raise ToolValidationError("session_id must be present")


def validate_open_url_payload(payload: Mapping[str, object], url_policy: UrlPolicy) -> None:
    raw = payload.get("url")
    if not isinstance(raw, str):
        raise ToolValidationError("open_url payload requires a url string")
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ToolValidationError("Only http and https URLs are allowed")
    url_policy.validate_url(raw)
