from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from schemas.api import (
    CapabilitiesResponse,
    ToolCallRequest,
    ToolCallResponse,
    ToolListResponse,
    ToolSchemasResponse,
)
from transport.base import ToolServiceBackend


def create_http_router(get_backend: Any) -> APIRouter:
    """HTTP transport routes for MCP-compatible tool operations."""

    router = APIRouter(prefix="/v1", tags=["mcp"])

    def backend(request: Request) -> ToolServiceBackend:
        return get_backend(request)

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/capabilities", response_model=CapabilitiesResponse)
    async def capabilities(service: ToolServiceBackend = Depends(backend)) -> CapabilitiesResponse:
        return service.get_capabilities()

    @router.get("/tools", response_model=ToolListResponse)
    async def list_tools(service: ToolServiceBackend = Depends(backend)) -> ToolListResponse:
        return service.list_tools()

    @router.get("/tools/schemas", response_model=ToolSchemasResponse)
    async def list_schemas(service: ToolServiceBackend = Depends(backend)) -> ToolSchemasResponse:
        return ToolSchemasResponse(schemas=service.list_schemas())

    @router.post("/tools/call", response_model=ToolCallResponse)
    async def call_tool(
        payload: ToolCallRequest,
        request: Request,
        service: ToolServiceBackend = Depends(backend),
    ) -> ToolCallResponse:
        correlation_id = payload.correlation_id or request.headers.get("X-Correlation-ID")
        payload.correlation_id = correlation_id
        try:
            result = await service.execute_tool(payload)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return ToolCallResponse(result=result, correlation_id=correlation_id)

    return router
