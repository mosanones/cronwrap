"""Configurable back-off strategies for retry delays."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Iterator


_STRATEGIES = ("fixed", "linear", "exponential")


@dataclass
class BackoffConfig:
    """Parameters that govern how retry delays are calculated."""

    strategy: str = "exponential"   # fixed | linear | exponential
    base_delay: float = 1.0          # seconds – starting delay
    max_delay: float = 300.0         # seconds – upper cap
    multiplier: float = 2.0          # used by linear and exponential
    jitter: bool = True              # add ±20 % random jitter

    def __post_init__(self) -> None:
        if self.strategy not in _STRATEGIES:
            raise ValueError(
                f"strategy must be one of {_STRATEGIES}, got {self.strategy!r}"
            )
        if self.base_delay <= 0:
            raise ValueError("base_delay must be > 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.multiplier <= 0:
            raise ValueError("multiplier must be > 0")


def _apply_jitter(delay: float) -> float:
    """Return *delay* ± up to 20 % random noise."""
    factor = 1.0 + random.uniform(-0.2, 0.2)
    return max(0.0, delay * factor)


def compute_delay(config: BackoffConfig, attempt: int) -> float:
    """Return the delay (seconds) before *attempt* (0-indexed).

    - ``fixed``       – always ``base_delay``
    - ``linear``      – ``base_delay + attempt * multiplier``
    - ``exponential`` – ``base_delay * multiplier ** attempt``
    """
    if config.strategy == "fixed":
        raw = config.base_delay
    elif config.strategy == "linear":
        raw = config.base_delay + attempt * config.multiplier
    else:  # exponential
        raw = config.base_delay * math.pow(config.multiplier, attempt)

    capped = min(raw, config.max_delay)
    return _apply_jitter(capped) if config.jitter else capped


def delay_sequence(config: BackoffConfig) -> Iterator[float]:
    """Yield an infinite sequence of back-off delays."""
    attempt = 0
    while True:
        yield compute_delay(config, attempt)
        attempt += 1
