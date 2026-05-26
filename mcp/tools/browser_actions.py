from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from browser_client.client import BrowserServiceClient
from registry.base import BaseTool, ToolExecutionContext
from schemas import (
    ClickElementPayload,
    CloseTabPayload,
    ExecuteJavaScriptPayload,
    ExtractLinksPayload,
    ExtractTablesPayload,
    ExtractTextPayload,
    GetDomSnapshotPayload,
    GetPageMetadataPayload,
    GoBackPayload,
    HoverElementPayload,
    OpenUrlPayload,
    PressKeyPayload,
    RefreshPagePayload,
    ScreenshotPayload,
    ScrollPagePayload,
    SelectDropdownPayload,
    SwitchTabPayload,
    ToolResult,
    TypeTextPayload,
    UploadFilePayload,
    WaitForElementPayload,
    SearchPayload,
)
from security.url_policy import UrlPolicy
from security.validation import sanitize_payload, validate_open_url_payload


class BrowserApiTool[ArgsT: BaseModel](BaseTool[ArgsT]):
    """Tool implementation that proxies execution to browser execution service."""

    def __init__(self, client: BrowserServiceClient) -> None:
        self._client = client

    async def _call_browser(self, context: ToolExecutionContext, payload: ArgsT) -> ToolResult:
        return await self._client.execute_action(
            session_id=context.session_id,
            action=self.name,
            payload=sanitize_payload(payload.model_dump(exclude_none=True)),
            correlation_id=context.correlation_id,
        )


class OpenUrlTool(BrowserApiTool[OpenUrlPayload]):
    name = "open_url"
    description = "Open an HTTP or HTTPS URL in the active browser session."
    input_schema = OpenUrlPayload

    def __init__(self, client: BrowserServiceClient, url_policy: UrlPolicy) -> None:
        super().__init__(client)
        self._url_policy = url_policy

    async def execute(self, context: ToolExecutionContext, payload: OpenUrlPayload) -> ToolResult:
        validate_open_url_payload(payload.model_dump(), self._url_policy)
        return await self._call_browser(context, payload)


def _tool_class(name: str, description: str, schema: type[BaseModel]) -> type[BrowserApiTool[Any]]:
    class _GeneratedTool(BrowserApiTool[Any]):
        input_schema = schema

        async def execute(self, context: ToolExecutionContext, payload: Any) -> ToolResult:
            return await self._call_browser(context, payload)

    _GeneratedTool.name = name
    _GeneratedTool.description = description
    _GeneratedTool.__name__ = f"{''.join(part.capitalize() for part in name.split('_'))}Tool"
    return _GeneratedTool


ClickElementTool = _tool_class(
    "click_element",
    "Click an actionable UI element using an opaque target reference.",
    ClickElementPayload,
)
TypeTextTool = _tool_class(
    "type_text",
    "Type text into an input-like element using an opaque target reference.",
    TypeTextPayload,
)
ExtractTextTool = _tool_class(
    "extract_text",
    "Extract visible text from page or selected semantic region.",
    ExtractTextPayload,
)
ScreenshotTool = _tool_class(
    "screenshot",
    "Capture a screenshot artifact from the browser service.",
    ScreenshotPayload,
)
GetDomSnapshotTool = _tool_class(
    "get_dom_snapshot",
    "Get compressed semantic page snapshot for planning.",
    GetDomSnapshotPayload,
)
WaitForElementTool = _tool_class(
    "wait_for_element",
    "Wait for a semantic element reference to appear.",
    WaitForElementPayload,
)
ScrollPageTool = _tool_class(
    "scroll_page",
    "Scroll the active page by direction and amount.",
    ScrollPagePayload,
)
GoBackTool = _tool_class(
    "go_back",
    "Navigate back in active tab history.",
    GoBackPayload,
)
HoverElementTool = _tool_class(
    "hover_element",
    "Hover over an element using an opaque target reference.",
    HoverElementPayload,
)
PressKeyTool = _tool_class(
    "press_key",
    "Press keyboard key with optional modifiers.",
    PressKeyPayload,
)
SelectDropdownTool = _tool_class(
    "select_dropdown",
    "Select option by value or label on dropdown control.",
    SelectDropdownPayload,
)
UploadFileTool = _tool_class(
    "upload_file",
    "Upload a file through a semantic file input target.",
    UploadFilePayload,
)
SwitchTabTool = _tool_class(
    "switch_tab",
    "Switch active browsing context to another tab.",
    SwitchTabPayload,
)
CloseTabTool = _tool_class(
    "close_tab",
    "Close current or selected tab.",
    CloseTabPayload,
)
RefreshPageTool = _tool_class(
    "refresh_page",
    "Refresh page, optionally forcing a hard reload.",
    RefreshPagePayload,
)
GetPageMetadataTool = _tool_class(
    "get_page_metadata",
    "Get metadata such as URL, title and viewport context.",
    GetPageMetadataPayload,
)
ExtractLinksTool = _tool_class(
    "extract_links",
    "Extract links from page with bounded result set.",
    ExtractLinksPayload,
)
ExtractTablesTool = _tool_class(
    "extract_tables",
    "Extract structured table data from visible page.",
    ExtractTablesPayload,
)
ExecuteJavaScriptTool = _tool_class(
    "execute_javascript",
    "Execute bounded custom JavaScript in current page context.",
    ExecuteJavaScriptPayload,
)


class SearchWebTool(BaseTool[SearchPayload]):
    name = "search_web"
    description = "Search the web via the browser search engine."
    input_schema = SearchPayload

    def __init__(self, client: BrowserServiceClient) -> None:
        self._client = client

    async def execute(self, context: ToolExecutionContext, payload: SearchPayload) -> ToolResult:
        return await self._client.execute_search(
            session_id=context.session_id,
            query=payload.query,
            correlation_id=context.correlation_id,
        )

