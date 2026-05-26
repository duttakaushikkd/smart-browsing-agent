from typing import Any

import pytest

from config.settings import Settings
from registry.base import ToolExecutionContext
from registry.registry import ToolRegistry
from schemas.responses import ToolResult
from security.url_policy import UrlPolicy
from tools.factory import create_browser_tools


class FakeBrowserServiceClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any], str | None]] = []

    async def execute_action(
        self,
        session_id: str,
        action: str,
        payload: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> ToolResult:
        self.calls.append((session_id, action, payload, correlation_id))
        return ToolResult(success=True, data={"ok": True})

    async def execute_search(
        self,
        session_id: str,
        query: str,
        *,
        correlation_id: str | None = None,
    ) -> ToolResult:
        self.calls.append((session_id, "search_web", {"query": query}, correlation_id))
        return ToolResult(success=True, data={"ok": True})


def _payloads() -> dict[str, dict[str, Any]]:
    return {
        "open_url": {"url": "https://example.com"},
        "click_element": {"target_ref": "el:1"},
        "type_text": {"target_ref": "el:1", "text": "hello"},
        "extract_text": {},
        "screenshot": {},
        "get_dom_snapshot": {},
        "wait_for_element": {"target_ref": "el:1"},
        "scroll_page": {},
        "go_back": {},
        "hover_element": {"target_ref": "el:1"},
        "press_key": {"key": "Enter"},
        "select_dropdown": {"target_ref": "el:1", "value": "x"},
        "upload_file": {"target_ref": "el:1", "file_path": "/tmp/a.txt"},
        "switch_tab": {"tab_id": "tab-1"},
        "close_tab": {},
        "refresh_page": {},
        "get_page_metadata": {},
        "extract_links": {},
        "extract_tables": {},
        "execute_javascript": {"script": "return 1;"},
        "search_web": {"query": "MacBook Air"},
    }


@pytest.mark.asyncio
async def test_registry_executes_all_tools() -> None:
    client = FakeBrowserServiceClient()
    registry = ToolRegistry(
        create_browser_tools(
            client=client,  # type: ignore[arg-type]
            url_policy=UrlPolicy(Settings(allowed_domains=["example.com"], blocked_domains=[])),
        )
    )
    context = ToolExecutionContext(session_id="session-123", correlation_id="corr-1")
    payloads = _payloads()
    assert set(registry.names()) == set(payloads)
    for name, payload in payloads.items():
        result = await registry.execute(name=name, arguments=payload, context=context)
        assert result.success is True
