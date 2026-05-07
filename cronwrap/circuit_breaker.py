"""Circuit breaker: pause a job after N consecutive failures."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CircuitBreakerConfig:
    max_failures: int = 3          # consecutive failures before opening
    reset_after: int = 300         # seconds before attempting half-open

    def __post_init__(self) -> None:
        if self.max_failures < 1:
            raise ValueError("max_failures must be >= 1")
        if self.reset_after < 0:
            raise ValueError("reset_after must be >= 0")


@dataclass
class CircuitState:
    job_name: str
    consecutive_failures: int = 0
    opened_at: Optional[str] = None   # ISO timestamp when circuit opened
    state: str = "closed"             # closed | open | half-open


class CircuitOpen(Exception):
    """Raised when the circuit is open and the job should be skipped."""


def _state_path(store_dir: str, job_name: str) -> str:
    safe = job_name.replace(os.sep, "_")
    return os.path.join(store_dir, f"{safe}.circuit.json")


def load_state(store_dir: str, job_name: str) -> CircuitState:
    path = _state_path(store_dir, job_name)
    try:
        with open(path) as fh:
            data = json.load(fh)
        return CircuitState(**data)
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return CircuitState(job_name=job_name)


def save_state(store_dir: str, state: CircuitState) -> None:
    os.makedirs(store_dir, exist_ok=True)
    path = _state_path(store_dir, state.job_name)
    with open(path, "w") as fh:
        json.dump(state.__dict__, fh)


def record_outcome(
    store_dir: str,
    job_name: str,
    success: bool,
    cfg: CircuitBreakerConfig,
    now_iso: str,
) -> CircuitState:
    """Update circuit state based on latest run outcome."""
    state = load_state(store_dir, job_name)
    if success:
        state.consecutive_failures = 0
        state.opened_at = None
        state.state = "closed"
    else:
        state.consecutive_failures += 1
        if state.consecutive_failures >= cfg.max_failures:
            state.state = "open"
            if state.opened_at is None:
                state.opened_at = now_iso
    save_state(store_dir, state)
    return state


def check_circuit(
    store_dir: str,
    job_name: str,
    cfg: CircuitBreakerConfig,
    now_ts: float,
) -> None:
    """Raise CircuitOpen if the circuit is open and reset window hasn't passed."""
    import datetime
    state = load_state(store_dir, job_name)
    if state.state != "open":
        return
    if state.opened_at:
        opened_dt = datetime.datetime.fromisoformat(state.opened_at)
        elapsed = now_ts - opened_dt.timestamp()
        if elapsed < cfg.reset_after:
            raise CircuitOpen(
                f"Circuit open for '{job_name}': "
                f"{int(cfg.reset_after - elapsed)}s remaining"
            )
        # allow half-open attempt
        state.state = "half-open"
        save_state(store_dir, state)
