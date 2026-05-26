from __future__ import annotations

import time
from typing import Any

import httpx
import structlog
from pydantic import AnyHttpUrl
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from browser_client.circuit_breaker import CircuitBreaker
from registry.exceptions import BrowserServiceError
from schemas.responses import ToolResult
from security.validation import ensure_action_allowed, sanitize_payload, validate_session_id

logger = structlog.get_logger(__name__)


class BrowserServiceClient:
    """Async HTTP client for external browser execution APIs."""

    def __init__(
        self,
        base_url: AnyHttpUrl,
        timeout_seconds: float,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self._base_url = str(base_url).rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._breaker = circuit_breaker or CircuitBreaker()
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2.0),
        reraise=True,
    )
    async def execute_action(
        self,
        session_id: str,
        action: str,
        payload: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> ToolResult:
        validate_session_id(session_id)
        ensure_action_allowed(action)
        request_body = {
            "session_id": session_id,
            "action": action,
            "payload": sanitize_payload(payload),
        }
        headers: dict[str, str] = {}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        self._breaker.before_call()
        started = time.perf_counter()
        try:
            response = await self._client.post(
                "/browser/action",
                json=request_body,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._breaker.record_failure()
            raise BrowserServiceError(
                f"Browser service HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except Exception:
            self._breaker.record_failure()
            raise

        self._breaker.record_success()
        try:
            parsed = ToolResult.model_validate(response.json())
        except ValueError as exc:
            raise BrowserServiceError("Invalid browser service response") from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        parsed.metadata = parsed.metadata | {
            "execution_time_ms": elapsed_ms,
            "action": action,
            "correlation_id": correlation_id,
        }
        logger.info(
            "browser_action_executed",
            action=action,
            session_id=session_id,
            success=parsed.success,
            execution_time_ms=elapsed_ms,
            correlation_id=correlation_id,
        )
        return parsed
