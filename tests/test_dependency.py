"""Tests for cronwrap.dependency."""
import json
import pytest
from pathlib import Path

from cronwrap.dependency import (
    DependencyGraph,
    add_dependency,
    get_dependencies,
    load_graph,
    remove_dependency,
    resolve_order,
    save_graph,
)


@pytest.fixture
def graph_path(tmp_path):
    return tmp_path / "deps.json"


def test_load_missing_file_returns_empty(graph_path):
    g = load_graph(graph_path)
    assert g.edges == {}


def test_load_corrupt_file_returns_empty(graph_path):
    graph_path.write_text("not json")
    g = load_graph(graph_path)
    assert g.edges == {}


def test_save_and_load_roundtrip(graph_path):
    g = DependencyGraph(edges={"b": ["a"]})
    save_graph(graph_path, g)
    loaded = load_graph(graph_path)
    assert loaded.edges == {"b": ["a"]}


def test_add_dependency_new_job():
    g = DependencyGraph()
    add_dependency(g, "b", "a")
    assert get_dependencies(g, "b") == ["a"]


def test_add_dependency_no_duplicates():
    g = DependencyGraph()
    add_dependency(g, "b", "a")
    add_dependency(g, "b", "a")
    assert get_dependencies(g, "b") == ["a"]


def test_remove_dependency():
    g = DependencyGraph(edges={"b": ["a", "c"]})
    remove_dependency(g, "b", "a")
    assert get_dependencies(g, "b") == ["c"]


def test_remove_nonexistent_dependency_is_noop():
    g = DependencyGraph(edges={"b": ["a"]})
    remove_dependency(g, "b", "z")
    assert get_dependencies(g, "b") == ["a"]


def test_get_dependencies_unknown_job():
    g = DependencyGraph()
    assert get_dependencies(g, "unknown") == []


def test_resolve_order_simple():
    g = DependencyGraph(edges={"b": ["a"], "c": ["b"]})
    order = resolve_order(g, ["c", "b", "a"])
    assert order.index("a") < order.index("b")
    assert order.index("b") < order.index("c")


def test_resolve_order_no_deps():
    g = DependencyGraph()
    order = resolve_order(g, ["x", "y"])
    assert set(order) == {"x", "y"}


def test_resolve_order_circular_raises():
    g = DependencyGraph(edges={"a": ["b"], "b": ["a"]})
    with pytest.raises(ValueError, match="Circular"):
        resolve_order(g, ["a", "b"])
