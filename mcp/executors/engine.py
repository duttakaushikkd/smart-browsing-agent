from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

from executors.errors import normalize_error
from registry.base import ToolExecutionContext
from registry.exceptions import ToolExecutionError, ToolTimeoutError
from registry.registry import ToolRegistry
from schemas.responses import ToolResult

logger = structlog.get_logger(__name__)


class ToolExecutorEngine:
    """Centralized tool execution with tracing, retries, and timeout handling."""

    def __init__(self, registry: ToolRegistry, timeout_seconds: float, max_retries: int) -> None:
        self._registry = registry
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    def openai_schemas(self) -> list[dict[str, Any]]:
        return self._registry.openai_schemas()

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolResult:
        attempt = 0
        while True:
            attempt += 1
            started = time.perf_counter()
            try:
                result = await asyncio.wait_for(
                    self._registry.execute(name=name, arguments=arguments, context=context),
                    timeout=self._timeout_seconds,
                )
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                result.metadata = result.metadata | {
                    "execution_time_ms": elapsed_ms,
                    "attempt": attempt,
                    "tool": name,
                    "correlation_id": context.correlation_id,
                }
                logger.info(
                    "tool_executed",
                    tool=name,
                    success=result.success,
                    attempt=attempt,
                    execution_time_ms=elapsed_ms,
                    session_id=context.session_id,
                    correlation_id=context.correlation_id,
                )
                return result
            except asyncio.TimeoutError as exc:
                logger.warning(
                    "tool_timeout",
                    tool=name,
                    attempt=attempt,
                    session_id=context.session_id,
                    correlation_id=context.correlation_id,
                )
                if attempt > self._max_retries:
                    return normalize_error(ToolTimeoutError(str(exc)))
            except Exception as exc:
                logger.warning(
                    "tool_execution_exception",
                    tool=name,
                    attempt=attempt,
                    session_id=context.session_id,
                    correlation_id=context.correlation_id,
                    error=str(exc),
                )
                if attempt > self._max_retries:
                    return normalize_error(ToolExecutionError(str(exc)))
                normalized = normalize_error(exc)
                if not normalized.metadata.get("recoverable", True):
                    return normalized
