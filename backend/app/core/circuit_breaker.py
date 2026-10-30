from dataclasses import dataclass
from time import monotonic


@dataclass
class CircuitBreaker:
    failure_limit: int = 3
    reset_after_seconds: float = 30.0
    failures: int = 0
    opened_at: float | None = None

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        if monotonic() - self.opened_at >= self.reset_after_seconds:
            self.failures = 0
            self.opened_at = None
            return "closed"
        return "open"

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_limit:
            self.opened_at = monotonic()


providers_breakers = {
    "geocoding": CircuitBreaker(),
    "weather": CircuitBreaker(),
    "routing": CircuitBreaker(),
    "elevation": CircuitBreaker(),
    "gemini": CircuitBreaker(),
}
