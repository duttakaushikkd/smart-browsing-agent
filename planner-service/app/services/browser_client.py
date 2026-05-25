from typing import Any

import httpx
from pydantic import AnyHttpUrl
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.schemas.tools import ToolResult
from app.services.circuit_breaker import CircuitBreaker


class BrowserServiceError(RuntimeError):
    """Raised when the external browser service returns an unusable response."""


class BrowserServiceClient:
    """HTTP wrapper for the external browser execution service.

    This client intentionally knows only the remote API contract. It imports no
    browser automation libraries and contains no DOM or Playwright execution logic.
    """

    def __init__(
        self,
        base_url: AnyHttpUrl,
        timeout_seconds: float,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self._base_url = str(base_url).rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._circuit_breaker = circuit_breaker or CircuitBreaker()

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2),
        reraise=True,
    )
    async def execute_action(
        self,
        session_id: str,
        action: str,
        payload: dict[str, Any],
    ) -> ToolResult:
        self._circuit_breaker.before_call()
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
                response = await client.post(
                    "/browser/action",
                    json={"session_id": session_id, "action": action, "payload": payload},
                )
                response.raise_for_status()
        except Exception:
            self._circuit_breaker.record_failure()
            raise

        self._circuit_breaker.record_success()
        try:
            return ToolResult.model_validate(response.json())
        except ValueError as exc:
            raise BrowserServiceError("Invalid browser service response") from exc
