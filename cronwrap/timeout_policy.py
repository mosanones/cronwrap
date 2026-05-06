"""Timeout policy: define escalating timeout tiers and classify execution results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TimeoutPolicy:
    """Defines soft and hard timeout thresholds for a job.

    soft_timeout_seconds: warn but do not kill the process.
    hard_timeout_seconds: kill the process and treat as failure.
    grace_period_seconds: extra time allowed after soft before hard fires.
    """

    soft_timeout_seconds: Optional[float] = None
    hard_timeout_seconds: Optional[float] = None
    grace_period_seconds: float = 5.0
    labels: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.soft_timeout_seconds is not None and self.soft_timeout_seconds <= 0:
            raise ValueError("soft_timeout_seconds must be positive")
        if self.hard_timeout_seconds is not None and self.hard_timeout_seconds <= 0:
            raise ValueError("hard_timeout_seconds must be positive")
        if (
            self.soft_timeout_seconds is not None
            and self.hard_timeout_seconds is not None
            and self.soft_timeout_seconds >= self.hard_timeout_seconds
        ):
            raise ValueError(
                "soft_timeout_seconds must be less than hard_timeout_seconds"
            )
        if self.grace_period_seconds < 0:
            raise ValueError("grace_period_seconds must be non-negative")

    def effective_hard_timeout(self) -> Optional[float]:
        """Return the hard timeout, accounting for grace period when only soft is set."""
        if self.hard_timeout_seconds is not None:
            return self.hard_timeout_seconds
        if self.soft_timeout_seconds is not None:
            return self.soft_timeout_seconds + self.grace_period_seconds
        return None

    def classify(self, elapsed: float) -> str:
        """Classify an elapsed duration as 'ok', 'soft_breach', or 'hard_breach'."""
        hard = self.effective_hard_timeout()
        if hard is not None and elapsed >= hard:
            return "hard_breach"
        if self.soft_timeout_seconds is not None and elapsed >= self.soft_timeout_seconds:
            return "soft_breach"
        return "ok"

    def summary(self) -> str:
        """Human-readable description of the policy."""
        parts = []
        if self.soft_timeout_seconds is not None:
            parts.append(f"soft={self.soft_timeout_seconds}s")
        if self.hard_timeout_seconds is not None:
            parts.append(f"hard={self.hard_timeout_seconds}s")
        if not parts:
            return "no timeout policy"
        parts.append(f"grace={self.grace_period_seconds}s")
        if self.labels:
            parts.append(f"labels={','.join(self.labels)}")
        return " | ".join(parts)
