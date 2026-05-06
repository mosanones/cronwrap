"""Tests for cronwrap.label_cli and cronwrap.label_hook."""
from pathlib import Path

import pytest

from cronwrap.label import save_label_index
from cronwrap.label_cli import render_all_labels, render_labels, render_search_results
from cronwrap.label_hook import apply_job_labels, get_job_labels, label_matches


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    return tmp_path / "labels.json"


# ── label_cli ────────────────────────────────────────────────────────────────

def test_render_labels_no_labels() -> None:
    result = render_labels("job_a", {})
    assert "job_a" in result
    assert "no labels" in result


def test_render_labels_sorted_keys() -> None:
    result = render_labels("job_a", {"z": "1", "a": "2"})
    assert result.index("a=") < result.index("z=")


def test_render_all_labels_empty_index() -> None:
    assert render_all_labels({}) == "(no labels defined)"


def test_render_all_labels_multiple_jobs() -> None:
    index = {"job_b": {"env": "prod"}, "job_a": {"team": "ops"}}
    result = render_all_labels(index)
    assert result.index("job_a") < result.index("job_b")


def test_render_search_results_no_match() -> None:
    result = render_search_results([], "env", "prod")
    assert "No jobs matched" in result
    assert "env=prod" in result


def test_render_search_results_key_only_query() -> None:
    result = render_search_results(["job_a"], "env", None)
    assert "'env'" in result
    assert "job_a" in result


def test_render_search_results_lists_all_jobs() -> None:
    result = render_search_results(["job_a", "job_b"], "env", "prod")
    assert "job_a" in result
    assert "job_b" in result


# ── label_hook ───────────────────────────────────────────────────────────────

def test_get_job_labels_missing_store(store: Path) -> None:
    assert get_job_labels("job_a", store) == {}


def test_apply_and_get_roundtrip(store: Path) -> None:
    apply_job_labels("job_a", {"env": "prod"}, store)
    assert get_job_labels("job_a", store) == {"env": "prod"}


def test_apply_merges_labels(store: Path) -> None:
    apply_job_labels("job_a", {"env": "prod"}, store)
    apply_job_labels("job_a", {"team": "ops"}, store)
    labels = get_job_labels("job_a", store)
    assert labels == {"env": "prod", "team": "ops"}


def test_label_matches_key_only_true(store: Path) -> None:
    apply_job_labels("job_a", {"env": "prod"}, store)
    assert label_matches("job_a", "env", store=store) is True


def test_label_matches_key_value_true(store: Path) -> None:
    apply_job_labels("job_a", {"env": "prod"}, store)
    assert label_matches("job_a", "env", "prod", store) is True


def test_label_matches_wrong_value(store: Path) -> None:
    apply_job_labels("job_a", {"env": "prod"}, store)
    assert label_matches("job_a", "env", "staging", store) is False


def test_label_matches_missing_key(store: Path) -> None:
    apply_job_labels("job_a", {"env": "prod"}, store)
    assert label_matches("job_a", "team", store=store) is False
