"""Format and render metrics summaries for CLI output."""
from __future__ import annotations

from typing import List

from cronwrap.metrics import MetricsSummary, load_metrics, summarise


def _bar(ratio: float, width: int = 20) -> str:
    filled = round(ratio * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render_summary(summary: MetricsSummary) -> str:
    lines = [
        f"Job: {summary.job_name}",
        f"  Total runs      : {summary.total_runs}",
        f"  Successful      : {summary.successful_runs}",
        f"  Failed          : {summary.failed_runs}",
        f"  Timed out       : {summary.timed_out_runs}",
        f"  Success rate    : {summary.success_rate * 100:.1f}% {_bar(summary.success_rate)}",
        f"  Avg duration    : {summary.avg_duration_seconds:.3f}s",
        f"  Min duration    : {summary.min_duration_seconds:.3f}s",
        f"  Max duration    : {summary.max_duration_seconds:.3f}s",
        f"  Last exit code  : {summary.last_exit_code}",
    ]
    return "\n".join(lines)


def render_all_summaries(metrics_path: str, job_names: List[str]) -> str:
    metrics = load_metrics(metrics_path)
    if not metrics:
        return "No metrics recorded yet."
    blocks = []
    for name in job_names:
        summary = summarise(name, metrics)
        if summary.total_runs > 0:
            blocks.append(render_summary(summary))
    return "\n\n".join(blocks) if blocks else "No metrics found for the given jobs."


def render_single_summary(metrics_path: str, job_name: str) -> str:
    metrics = load_metrics(metrics_path)
    summary = summarise(job_name, metrics)
    if summary.total_runs == 0:
        return f"No metrics recorded for job '{job_name}'."
    return render_summary(summary)
