"""Per-job execution quota enforcement (max runs per calendar period)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List


@dataclass
class QuotaConfig:
    max_runs: int
    period: str  # "hourly" | "daily" | "weekly" | "monthly"

    def __post_init__(self) -> None:
        if self.max_runs < 1:
            raise ValueError("max_runs must be >= 1")
        valid = {"hourly", "daily", "weekly", "monthly"}
        if self.period not in valid:
            raise ValueError(f"period must be one of {valid}")

    def period_key(self, dt: datetime | None = None) -> str:
        """Return a string key identifying the current period bucket."""
        now = dt or datetime.now(timezone.utc)
        if self.period == "hourly":
            return now.strftime("%Y-%m-%dT%H")
        if self.period == "daily":
            return now.strftime("%Y-%m-%d")
        if self.period == "weekly":
            # ISO week
            return now.strftime("%Y-W%W")
        # monthly
        return now.strftime("%Y-%m")


class QuotaExceeded(Exception):
    """Raised when a job has exhausted its quota for the current period."""


@dataclass
class _QuotaState:
    period_key: str
    runs: int = 0
    timestamps: List[str] = field(default_factory=list)


def _state_path(job_name: str, base_dir: str | None = None) -> Path:
    base = Path(base_dir) if base_dir else Path(os.environ.get("CRONWRAP_DATA_DIR", ".cronwrap"))
    base.mkdir(parents=True, exist_ok=True)
    return base / f"quota_{job_name}.json"


def check_quota(job_name: str, config: QuotaConfig, base_dir: str | None = None) -> None:
    """Check and increment quota. Raises QuotaExceeded if limit is reached."""
    path = _state_path(job_name, base_dir)
    now = datetime.now(timezone.utc)
    key = config.period_key(now)

    state: _QuotaState
    if path.exists():
        try:
            raw = json.loads(path.read_text())
            state = _QuotaState(**raw)
        except Exception:
            state = _QuotaState(period_key=key)
    else:
        state = _QuotaState(period_key=key)

    # Reset if we're in a new period
    if state.period_key != key:
        state = _QuotaState(period_key=key)

    if state.runs >= config.max_runs:
        raise QuotaExceeded(
            f"Job '{job_name}' has reached its quota of {config.max_runs} "
            f"runs for {config.period} period '{key}'."
        )

    state.runs += 1
    state.timestamps.append(now.isoformat())
    path.write_text(json.dumps(state.__dict__))


def load_quota_state(job_name: str, base_dir: str | None = None) -> _QuotaState | None:
    """Return the current quota state for a job, or None if no state exists."""
    path = _state_path(job_name, base_dir)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
        return _QuotaState(**raw)
    except Exception:
        return None
