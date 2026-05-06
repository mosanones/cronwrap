"""Tests for cronwrap.dependency_hook and cronwrap.dependency_cli."""
import json
import pytest
from pathlib import Path

from cronwrap.dependency import DependencyGraph, add_dependency, load_graph
from cronwrap.dependency_hook import DependencyNotMet, check_dependencies
from cronwrap.dependency_cli import (
    cmd_add,
    cmd_remove,
    render_dependencies,
    render_order,
)


@pytest.fixture
def history_path(tmp_path):
    return tmp_path / "history.json"


@pytest.fixture
def graph_path(tmp_path):
    return tmp_path / "deps.json"


def _write_history(path, records):
    path.write_text(json.dumps(records))


# --- dependency_hook tests ---

def test_check_no_dependencies_passes(history_path):
    g = DependencyGraph()
    check_dependencies("job_a", g, history_path)  # should not raise


def test_check_dependency_success_passes(history_path):
    _write_history(history_path, [{"job": "upstream", "status": "success", "timestamp": "2024-01-01T00:00:00"}])
    g = DependencyGraph(edges={"job_b": ["upstream"]})
    check_dependencies("job_b", g, history_path)  # should not raise


def test_check_dependency_failure_raises(history_path):
    _write_history(history_path, [{"job": "upstream", "status": "failure", "timestamp": "2024-01-01T00:00:00"}])
    g = DependencyGraph(edges={"job_b": ["upstream"]})
    with pytest.raises(DependencyNotMet, match="upstream"):
        check_dependencies("job_b", g, history_path)


def test_check_dependency_missing_history_raises(history_path):
    g = DependencyGraph(edges={"job_b": ["upstream"]})
    with pytest.raises(DependencyNotMet):
        check_dependencies("job_b", g, history_path)


def test_check_uses_most_recent_record(history_path):
    _write_history(history_path, [
        {"job": "upstream", "status": "failure", "timestamp": "2024-01-01T00:00:00"},
        {"job": "upstream", "status": "success", "timestamp": "2024-01-02T00:00:00"},
    ])
    g = DependencyGraph(edges={"job_b": ["upstream"]})
    check_dependencies("job_b", g, history_path)  # latest is success, should pass


# --- dependency_cli tests ---

def test_render_dependencies_no_deps():
    g = DependencyGraph()
    out = render_dependencies("job_a", g)
    assert "no dependencies" in out


def test_render_dependencies_with_deps():
    g = DependencyGraph(edges={"job_b": ["job_a"]})
    out = render_dependencies("job_b", g)
    assert "job_a" in out


def test_render_order_valid():
    g = DependencyGraph(edges={"b": ["a"]})
    out = render_order(["a", "b"], g)
    assert "a" in out and "b" in out
    assert out.index("a") < out.index("b")


def test_render_order_circular_shows_error():
    g = DependencyGraph(edges={"a": ["b"], "b": ["a"]})
    out = render_order(["a", "b"], g)
    assert "Error" in out


def test_cmd_add_persists(graph_path):
    g = DependencyGraph()
    msg = cmd_add(g, graph_path, "job_b", "job_a")
    assert "job_a" in msg
    loaded = load_graph(graph_path)
    assert "job_a" in loaded.edges.get("job_b", [])


def test_cmd_remove_persists(graph_path):
    g = DependencyGraph(edges={"job_b": ["job_a"]})
    cmd_remove(g, graph_path, "job_b", "job_a")
    loaded = load_graph(graph_path)
    assert "job_a" not in loaded.edges.get("job_b", [])
