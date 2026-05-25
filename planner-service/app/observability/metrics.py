from dataclasses import dataclass, field
from time import perf_counter


@dataclass(slots=True)
class ExecutionTimer:
    """Simple timer for latency accounting."""

    started_at: float = field(default_factory=perf_counter)

    @property
    def elapsed_ms(self) -> float:
        return (perf_counter() - self.started_at) * 1000
