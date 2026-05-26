from __future__ import annotations

from typing import cast

from fastapi import Request

from server.runtime import McpToolService


def get_tool_service(request: Request) -> McpToolService:
    return cast(McpToolService, request.app.state.tool_service)
