from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def trace_span(name: str, **fields: Any) -> AsyncIterator[dict[str, Any]]:
    """Lightweight span helper for distributed tracing metadata."""

    started = time.perf_counter()
    span: dict[str, Any] = {"span": name, **fields}
    logger.info("span_started", **span)
    try:
        yield span
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        span["duration_ms"] = elapsed_ms
        logger.info("span_finished", **span)
