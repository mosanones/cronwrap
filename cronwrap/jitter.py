"""Jitter support: add randomised delay before job execution to avoid thundering-herd."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JitterConfig:
    """Configuration for pre-execution jitter delay."""

    max_seconds: float = 0.0
    min_seconds: float = 0.0
    seed: Optional[int] = None  # for deterministic testing

    def __post_init__(self) -> None:
        if self.min_seconds < 0:
            raise ValueError("min_seconds must be >= 0")
        if self.max_seconds < 0:
            raise ValueError("max_seconds must be >= 0")
        if self.min_seconds > self.max_seconds:
            raise ValueError("min_seconds must be <= max_seconds")

    @property
    def enabled(self) -> bool:
        return self.max_seconds > 0


def sample_delay(config: JitterConfig) -> float:
    """Return a random delay (in seconds) drawn from [min_seconds, max_seconds]."""
    if not config.enabled:
        return 0.0
    rng = random.Random(config.seed)
    return rng.uniform(config.min_seconds, config.max_seconds)


def apply_jitter(config: JitterConfig, *, _sleep=time.sleep) -> float:
    """Sleep for a jittered duration and return the actual delay applied.

    Parameters
    ----------
    config:
        JitterConfig instance describing the desired delay range.
    _sleep:
        Injectable sleep callable (default: ``time.sleep``); override in tests.

    Returns
    -------
    float
        The number of seconds slept.
    """
    delay = sample_delay(config)
    if delay > 0:
        _sleep(delay)
    return delay
