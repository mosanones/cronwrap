"""Job dependency tracking: define and resolve inter-job dependencies."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DependencyGraph:
    """Maps each job name to the list of job names it depends on."""
    edges: Dict[str, List[str]] = field(default_factory=dict)


def load_graph(path: Path) -> DependencyGraph:
    """Load dependency graph from *path*; return empty graph on missing/corrupt file."""
    try:
        data = json.loads(path.read_text())
        return DependencyGraph(edges={str(k): list(v) for k, v in data.items()})
    except (FileNotFoundError, json.JSONDecodeError, AttributeError, TypeError):
        return DependencyGraph()


def save_graph(path: Path, graph: DependencyGraph) -> None:
    """Persist *graph* to *path* as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph.edges, indent=2))


def add_dependency(graph: DependencyGraph, job: str, depends_on: str) -> None:
    """Record that *job* depends on *depends_on*."""
    deps = graph.edges.setdefault(job, [])
    if depends_on not in deps:
        deps.append(depends_on)


def remove_dependency(graph: DependencyGraph, job: str, depends_on: str) -> None:
    """Remove a single dependency edge; no-op if it does not exist."""
    if job in graph.edges:
        graph.edges[job] = [d for d in graph.edges[job] if d != depends_on]


def get_dependencies(graph: DependencyGraph, job: str) -> List[str]:
    """Return direct dependencies of *job*."""
    return list(graph.edges.get(job, []))


def _topo_visit(
    job: str,
    graph: DependencyGraph,
    visited: set,
    stack: list,
    path: Optional[set] = None,
) -> None:
    if path is None:
        path = set()
    if job in path:
        raise ValueError(f"Circular dependency detected involving job '{job}'")
    if job in visited:
        return
    path.add(job)
    for dep in graph.edges.get(job, []):
        _topo_visit(dep, graph, visited, stack, path)
    path.discard(job)
    visited.add(job)
    stack.append(job)


def resolve_order(graph: DependencyGraph, jobs: List[str]) -> List[str]:
    """Return *jobs* in topological order (dependencies first).

    Raises ValueError on circular dependencies.
    """
    visited: set = set()
    stack: list = []
    for job in jobs:
        _topo_visit(job, graph, visited, stack)
    # Return only the jobs originally requested, preserving topo order
    requested = set(jobs)
    return [j for j in stack if j in requested]
