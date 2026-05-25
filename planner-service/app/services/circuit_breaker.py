from datetime import UTC, datetime, timedelta
from enum import StrEnum


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(RuntimeError):
    """Raised when a dependency is temporarily unavailable."""


class CircuitBreaker:
    """Small async-safe-enough circuit breaker for per-process dependency protection."""

    def __init__(self, failure_threshold: int = 5, recovery_seconds: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at: datetime | None = None

    def before_call(self) -> None:
        if self.state != CircuitState.OPEN:
            return
        assert self.opened_at is not None
        if datetime.now(UTC) - self.opened_at > timedelta(seconds=self.recovery_seconds):
            self.state = CircuitState.HALF_OPEN
            return
        raise CircuitBreakerOpen("Circuit breaker is open")

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = datetime.now(UTC)
