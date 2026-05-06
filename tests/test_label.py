"""Tests for cronwrap.label — label index CRUD and search."""
import json
from pathlib import Path

import pytest

from cronwrap.label import (
    find_jobs_by_label,
    get_labels,
    load_label_index,
    remove_labels,
    save_label_index,
    set_labels,
)


@pytest.fixture()
def label_path(tmp_path: Path) -> Path:
    return tmp_path / "labels.json"


def test_load_missing_file_returns_empty(label_path: Path) -> None:
    assert load_label_index(label_path) == {}


def test_load_corrupt_file_returns_empty(label_path: Path) -> None:
    label_path.write_text("not json{{{")
    assert load_label_index(label_path) == {}


def test_load_wrong_type_returns_empty(label_path: Path) -> None:
    label_path.write_text(json.dumps(["a", "b"]))
    assert load_label_index(label_path) == {}


def test_save_and_load_roundtrip(label_path: Path) -> None:
    index = {"job_a": {"env": "prod", "team": "ops"}}
    save_label_index(label_path, index)
    assert load_label_index(label_path) == index


def test_set_labels_creates_new_job() -> None:
    index = set_labels({}, "job_a", {"env": "prod"})
    assert index == {"job_a": {"env": "prod"}}


def test_set_labels_merges_existing() -> None:
    index = {"job_a": {"env": "prod"}}
    index = set_labels(index, "job_a", {"team": "ops"})
    assert index["job_a"] == {"env": "prod", "team": "ops"}


def test_set_labels_overwrites_key() -> None:
    index = {"job_a": {"env": "prod"}}
    index = set_labels(index, "job_a", {"env": "staging"})
    assert index["job_a"]["env"] == "staging"


def test_remove_labels_drops_keys() -> None:
    index = {"job_a": {"env": "prod", "team": "ops"}}
    index = remove_labels(index, "job_a", ["team"])
    assert index == {"job_a": {"env": "prod"}}


def test_remove_labels_removes_job_when_empty() -> None:
    index = {"job_a": {"env": "prod"}}
    index = remove_labels(index, "job_a", ["env"])
    assert "job_a" not in index


def test_remove_labels_ignores_missing_keys() -> None:
    index = {"job_a": {"env": "prod"}}
    index = remove_labels(index, "job_a", ["nonexistent"])
    assert index == {"job_a": {"env": "prod"}}


def test_get_labels_returns_empty_for_unknown() -> None:
    assert get_labels({}, "job_x") == {}


def test_find_jobs_by_label_key_only() -> None:
    index = {
        "job_a": {"env": "prod"},
        "job_b": {"env": "staging"},
        "job_c": {"team": "ops"},
    }
    assert find_jobs_by_label(index, "env") == ["job_a", "job_b"]


def test_find_jobs_by_label_key_and_value() -> None:
    index = {
        "job_a": {"env": "prod"},
        "job_b": {"env": "staging"},
    }
    assert find_jobs_by_label(index, "env", "prod") == ["job_a"]


def test_find_jobs_by_label_no_match() -> None:
    assert find_jobs_by_label({"job_a": {"env": "prod"}}, "team") == []
