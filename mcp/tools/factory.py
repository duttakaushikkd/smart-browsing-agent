from __future__ import annotations

from typing import Any

from browser_client.client import BrowserServiceClient
from registry.base import BaseTool
from security.url_policy import UrlPolicy
from tools.browser_actions import (
    ClickElementTool,
    CloseTabTool,
    ExecuteJavaScriptTool,
    ExtractLinksTool,
    ExtractTablesTool,
    ExtractTextTool,
    GetDomSnapshotTool,
    GetPageMetadataTool,
    GoBackTool,
    HoverElementTool,
    OpenUrlTool,
    PressKeyTool,
    RefreshPageTool,
    ScreenshotTool,
    ScrollPageTool,
    SelectDropdownTool,
    SwitchTabTool,
    TypeTextTool,
    UploadFileTool,
    WaitForElementTool,
    SearchWebTool,
)


def create_browser_tools(client: BrowserServiceClient, url_policy: UrlPolicy) -> list[BaseTool[Any]]:
    """Register all browser-facing MCP tools."""

    return [
        OpenUrlTool(client, url_policy),
        ClickElementTool(client),
        TypeTextTool(client),
        ExtractTextTool(client),
        ScreenshotTool(client),
        GetDomSnapshotTool(client),
        WaitForElementTool(client),
        ScrollPageTool(client),
        GoBackTool(client),
        HoverElementTool(client),
        PressKeyTool(client),
        SelectDropdownTool(client),
        UploadFileTool(client),
        SwitchTabTool(client),
        CloseTabTool(client),
        RefreshPageTool(client),
        GetPageMetadataTool(client),
        ExtractLinksTool(client),
        ExtractTablesTool(client),
        ExecuteJavaScriptTool(client),
        SearchWebTool(client),
    ]


def register_tools() -> list[BaseTool[Any]]:
    """Plugin-style registration hook for autodiscovery."""

    raise RuntimeError("register_tools requires runtime dependencies; use create_browser_tools instead")
