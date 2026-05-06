"""CLI helpers for displaying and querying job labels."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from cronwrap.label import LabelIndex, find_jobs_by_label, get_labels


def render_labels(job_name: str, labels: Dict[str, str]) -> str:
    """Return a human-readable block of labels for *job_name*."""
    if not labels:
        return f"{job_name}: (no labels)"
    lines = [f"{job_name}:"]
    for k, v in sorted(labels.items()):
        lines.append(f"  {k}={v}")
    return "\n".join(lines)


def render_all_labels(index: LabelIndex) -> str:
    """Return a human-readable summary of all labelled jobs."""
    if not index:
        return "(no labels defined)"
    blocks = [render_labels(job, labels) for job, labels in sorted(index.items())]
    return "\n".join(blocks)


def render_search_results(jobs: List[str], key: str, value: Optional[str]) -> str:
    """Return a formatted list of jobs matching a label query."""
    query = key if value is None else f"{key}={value}"
    if not jobs:
        return f"No jobs matched label '{query}'."
    header = f"Jobs with label '{query}':"
    return "\n".join([header] + [f"  - {j}" for j in jobs])
