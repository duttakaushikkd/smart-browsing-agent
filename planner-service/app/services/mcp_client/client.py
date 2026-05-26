from __future__ import annotations

import time
import uuid
from typing import Any

import httpx
import structlog
from pydantic import AnyHttpUrl
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.schemas.tools import ToolResult
from app.services.mcp_client.exceptions import McpResponseError, McpTransportError
from app.services.mcp_client.protocol import (
    McpToolCallRequest,
    McpToolCallResponse,
    McpToolListResponse,
    ToolExecutionContext,
)

logger = structlog.get_logger(__name__)


class McpClient:
    """Remote MCP tool client used by the planner (HTTP transport)."""

    def __init__(
        self,
        base_url: AnyHttpUrl,
        timeout_seconds: float,
        max_retries: int = 2,
    ) -> None:
        self._base_url = str(base_url).rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        self._schema_cache: list[dict[str, Any]] | None = None

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2.0),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> httpx.Response:
        headers: dict[str, str] = {}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        try:
            response = await self._client.request(method, path, json=json, headers=headers)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            raise McpTransportError(
                f"MCP HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise McpTransportError(str(exc)) from exc

    async def discover_tools(self, *, refresh: bool = False) -> McpToolListResponse:
        if not refresh:
            cached = getattr(self, "_tools_cache", None)
            if cached is not None:
                return cached
        response = await self._request("GET", "/v1/tools")
        try:
            payload = McpToolListResponse.model_validate(response.json())
        except ValueError as exc:
            raise McpResponseError("Invalid MCP tool list response") from exc
        self._tools_cache = payload
        return payload

    async def get_tool_schemas(self, *, refresh: bool = False) -> list[dict[str, Any]]:
        if self._schema_cache is not None and not refresh:
            return self._schema_cache
        response = await self._request("GET", "/v1/tools/schemas")
        try:
            schemas = response.json().get("schemas", [])
            if not isinstance(schemas, list):
                raise ValueError("schemas must be a list")
            self._schema_cache = schemas
            return schemas
        except (ValueError, AttributeError) as exc:
            raise McpResponseError("Invalid MCP schema response") from exc

    async def execute_tool(
        self,
        tool_name: str,
        payload: dict[str, Any],
        *,
        session_id: str,
        correlation_id: str | None = None,
    ) -> ToolResult:
        correlation_id = correlation_id or str(uuid.uuid4())
        request = McpToolCallRequest(
            session_id=session_id,
            tool_name=tool_name,
            arguments=payload,
            correlation_id=correlation_id,
        )
        started = time.perf_counter()
        response = await self._request(
            "POST",
            "/v1/tools/call",
            json=request.model_dump(),
            correlation_id=correlation_id,
        )
        try:
            parsed = McpToolCallResponse.model_validate(response.json())
        except ValueError as exc:
            raise McpResponseError("Invalid MCP tool call response") from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        parsed.result.metadata = parsed.result.metadata | {
            "mcp_execution_time_ms": elapsed_ms,
            "correlation_id": correlation_id,
            "transport": "http",
        }
        logger.info(
            "mcp_tool_executed",
            tool=tool_name,
            session_id=session_id,
            success=parsed.result.success,
            execution_time_ms=elapsed_ms,
            correlation_id=correlation_id,
        )
        return parsed.result

    def openai_schemas(self) -> list[dict[str, Any]]:
        if self._schema_cache is None:
            raise McpResponseError("Tool schemas not loaded; call get_tool_schemas() first")
        return self._schema_cache


class McpToolExecutor:
    """Planner-facing adapter with the same execution surface as the former local executor."""

    def __init__(self, client: McpClient) -> None:
        self._client = client

    def openai_schemas(self) -> list[dict[str, Any]]:
        return self._client.openai_schemas()

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        try:
            return await self._client.execute_tool(
                tool_name=name,
                payload=arguments,
                session_id=context.session_id,
                correlation_id=context.correlation_id,
            )
        except McpTransportError as exc:
            return ToolResult(success=False, error=str(exc), metadata={"recoverable": True, "mcp": True})
        except McpResponseError as exc:
            return ToolResult(success=False, error=str(exc), metadata={"recoverable": False, "mcp": True})
