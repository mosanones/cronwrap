"""Cron expression parsing and next-run scheduling utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day": (1, 31),
    "month": (1, 12),
    "weekday": (0, 6),
}


@dataclass
class CronExpression:
    raw: str
    minute: list[int]
    hour: list[int]
    day: list[int]
    month: list[int]
    weekday: list[int]

    @classmethod
    def parse(cls, expression: str) -> "CronExpression":
        """Parse a standard 5-field cron expression."""
        fields = expression.strip().split()
        if len(fields) != 5:
            raise ValueError(
                f"Expected 5 cron fields, got {len(fields)}: {expression!r}"
            )
        names = list(_FIELD_RANGES.keys())
        parsed = {
            name: _parse_field(field, *_FIELD_RANGES[name])
            for name, field in zip(names, fields)
        }
        return cls(raw=expression, **parsed)

    def matches(self, dt: datetime) -> bool:
        """Return True if *dt* satisfies this cron expression."""
        return (
            dt.minute in self.minute
            and dt.hour in self.hour
            and dt.day in self.day
            and dt.month in self.month
            and dt.weekday() in self.weekday
        )

    def next_run(self, after: Optional[datetime] = None) -> datetime:
        """Return the next datetime (minute precision) that matches."""
        dt = (after or datetime.now()).replace(second=0, microsecond=0)
        dt += timedelta(minutes=1)
        for _ in range(527040):  # max 1 year of minutes
            if self.matches(dt):
                return dt
            dt += timedelta(minutes=1)
        raise RuntimeError("Could not find next run within one year")


def _parse_field(field: str, lo: int, hi: int) -> list[int]:
    """Expand a single cron field into a sorted list of integers."""
    if field == "*":
        return list(range(lo, hi + 1))
    values: set[int] = set()
    for part in field.split(","):
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            start = lo if base == "*" else int(base.split("-")[0])
            end = hi if base == "*" else (int(base.split("-")[1]) if "-" in base else start)
            values.update(range(start, end + 1, step))
        elif "-" in part:
            a, b = part.split("-", 1)
            values.update(range(int(a), int(b) + 1))
        else:
            values.add(int(part))
    invalid = [v for v in values if not (lo <= v <= hi)]
    if invalid:
        raise ValueError(f"Values {invalid} out of range [{lo}, {hi}]")
    return sorted(values)
