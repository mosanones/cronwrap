"""Hook that checks whether a job's dependencies have succeeded recently."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from cronwrap.dependency import DependencyGraph, get_dependencies
from cronwrap.history import load_history


class DependencyNotMet(Exception):
    """Raised when one or more upstream jobs have not completed successfully."""


def check_dependencies(
    job: str,
    graph: DependencyGraph,
    history_path: Path,
    required_status: str = "success",
) -> None:
    """Raise DependencyNotMet if any dependency of *job* has not run successfully.

    Only the most recent run of each dependency is inspected.
    """
    deps = get_dependencies(graph, job)
    if not deps:
        return

    history = load_history(history_path)
    # Build a map: job_name -> latest record
    latest: dict = {}
    for record in history:
        name = record.get("job")
        if name and (name not in latest or record.get("timestamp", "") > latest[name].get("timestamp", "")):
            latest[name] = record

    unmet: List[str] = []
    for dep in deps:
        rec = latest.get(dep)
        if rec is None or rec.get("status") != required_status:
            unmet.append(dep)

    if unmet:
        raise DependencyNotMet(
            f"Job '{job}' cannot run: unmet dependencies: {', '.join(unmet)}"
        )
