from __future__ import annotations

import asyncio

from pydantic import ValidationError

from registry.exceptions import (
    BrowserServiceError,
    CircuitOpenError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolUnavailableError,
    ToolValidationError,
)
from schemas.responses import ToolResult


def normalize_error(exc: Exception) -> ToolResult:
    if isinstance(exc, ToolUnavailableError):
        return ToolResult(success=False, error=str(exc), metadata={"recoverable": False})
    if isinstance(exc, (ToolValidationError, ValidationError)):
        return ToolResult(success=False, error=str(exc), metadata={"recoverable": True})
    if isinstance(exc, (ToolTimeoutError, asyncio.TimeoutError)):
        return ToolResult(
            success=False,
            error="Tool execution timed out",
            metadata={"recoverable": True},
        )
    if isinstance(exc, CircuitOpenError):
        return ToolResult(
            success=False,
            error=str(exc),
            metadata={"recoverable": True, "circuit_open": True},
        )
    if isinstance(exc, BrowserServiceError):
        return ToolResult(
            success=False,
            error=str(exc),
            metadata={"recoverable": True, "external": True},
        )
    if isinstance(exc, ToolExecutionError):
        return ToolResult(success=False, error=str(exc), metadata={"recoverable": True})
    return ToolResult(
        success=False,
        error=f"Unexpected tool failure: {exc}",
        metadata={"recoverable": True},
    )
