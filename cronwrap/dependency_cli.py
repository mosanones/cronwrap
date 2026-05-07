"""CLI helpers for inspecting and managing job dependencies."""
from __future__ import annotations

from pathlib import Path
from typing import List

from cronwrap.dependency import (
    DependencyGraph,
    add_dependency,
    get_dependencies,
    remove_dependency,
    resolve_order,
    save_graph,
)


def render_dependencies(job: str, graph: DependencyGraph) -> str:
    """Return a human-readable list of direct dependencies for *job*."""
    deps = get_dependencies(graph, job)
    if not deps:
        return f"Job '{job}' has no dependencies."
    lines = [f"Dependencies for '{job}':"]
    for dep in deps:
        lines.append(f"  - {dep}")
    return "\n".join(lines)


def render_order(jobs: List[str], graph: DependencyGraph) -> str:
    """Return a human-readable resolved execution order for *jobs*."""
    try:
        ordered = resolve_order(graph, jobs)
    except ValueError as exc:
        return f"Error: {exc}"
    lines = ["Resolved execution order:"]
    for i, job in enumerate(ordered, 1):
        lines.append(f"  {i}. {job}")
    return "\n".join(lines)


def cmd_add(graph: DependencyGraph, path: Path, job: str, depends_on: str) -> str:
    """Add a dependency edge and persist the graph.

    Returns an error message string if *job* and *depends_on* are the same,
    to prevent self-referential dependency entries.
    """
    if job == depends_on:
        return f"Error: '{job}' cannot depend on itself."
    add_dependency(graph, job, depends_on)
    save_graph(path, graph)
    return f"Added: '{job}' depends on '{depends_on}'."


def cmd_remove(graph: DependencyGraph, path: Path, job: str, depends_on: str) -> str:
    """Remove a dependency edge and persist the graph."""
    remove_dependency(graph, job, depends_on)
    save_graph(path, graph)
    return f"Removed dependency of '{job}' on '{depends_on}'."
