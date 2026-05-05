"""Lightweight metrics collection for cron job runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class JobMetric:
    job_name: str
    timestamp: str
    duration_seconds: float
    exit_code: int
    attempt: int
    timed_out: bool
    success: bool


@dataclass
class MetricsSummary:
    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    timed_out_runs: int = 0
    avg_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    min_duration_seconds: float = float("inf")
    last_exit_code: Optional[int] = None
    durations: List[float] = field(default_factory=list, repr=False)

    def ingest(self, metric: JobMetric) -> None:
        self.total_runs += 1
        if metric.success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
        if metric.timed_out:
            self.timed_out_runs += 1
        self.durations.append(metric.duration_seconds)
        self.max_duration_seconds = max(self.max_duration_seconds, metric.duration_seconds)
        self.min_duration_seconds = min(self.min_duration_seconds, metric.duration_seconds)
        self.avg_duration_seconds = sum(self.durations) / len(self.durations)
        self.last_exit_code = metric.exit_code

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs


def load_metrics(path: str) -> List[JobMetric]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as fh:
            raw = json.load(fh)
        return [JobMetric(**item) for item in raw]
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def save_metrics(path: str, metrics: List[JobMetric]) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump([asdict(m) for m in metrics], fh, indent=2)


def append_metric(path: str, metric: JobMetric) -> None:
    existing = load_metrics(path)
    existing.append(metric)
    save_metrics(path, existing)


def summarise(job_name: str, metrics: List[JobMetric]) -> MetricsSummary:
    summary = MetricsSummary(job_name=job_name)
    for m in metrics:
        if m.job_name == job_name:
            summary.ingest(m)
    if summary.total_runs == 0:
        summary.min_duration_seconds = 0.0
    return summary
