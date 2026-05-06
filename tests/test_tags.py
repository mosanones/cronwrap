"""Tests for cronwrap.tags — tag-based job filtering."""
import json
import pytest
from pathlib import Path

from cronwrap.tags import (
    TagIndex,
    load_tag_index,
    save_tag_index,
    add_job_tags,
    remove_job_tags,
    jobs_for_tag,
    tags_for_job,
)


@pytest.fixture
def tag_path(tmp_path: Path) -> Path:
    return tmp_path / "tags.json"


# --- load / save ---

def test_load_missing_file_returns_empty(tag_path: Path):
    result = load_tag_index(tag_path)
    assert result.index == {}


def test_load_corrupt_file_returns_empty(tag_path: Path):
    tag_path.write_text("not valid json{{{")
    result = load_tag_index(tag_path)
    assert result.index == {}


def test_save_and_load_roundtrip(tag_path: Path):
    ti = TagIndex(index={"nightly": ["backup", "report"], "critical": ["backup"]})
    save_tag_index(tag_path, ti)
    loaded = load_tag_index(tag_path)
    assert loaded.index == ti.index


# --- add_job_tags ---

def test_add_job_tags_creates_new_tag():
    ti = TagIndex()
    ti2 = add_job_tags(ti, "backup", ["nightly"])
    assert "backup" in ti2.index["nightly"]


def test_add_job_tags_no_duplicates():
    ti = TagIndex(index={"nightly": ["backup"]})
    ti2 = add_job_tags(ti, "backup", ["nightly"])
    assert ti2.index["nightly"].count("backup") == 1


def test_add_job_tags_multiple_tags():
    ti = TagIndex()
    ti2 = add_job_tags(ti, "report", ["nightly", "critical"])
    assert "report" in ti2.index["nightly"]
    assert "report" in ti2.index["critical"]


def test_add_job_tags_does_not_mutate_original():
    ti = TagIndex()
    add_job_tags(ti, "backup", ["nightly"])
    assert ti.index == {}


# --- remove_job_tags ---

def test_remove_job_from_specific_tag():
    ti = TagIndex(index={"nightly": ["backup", "report"], "critical": ["backup"]})
    ti2 = remove_job_tags(ti, "backup", ["nightly"])
    assert "backup" not in ti2.index.get("nightly", [])
    assert "backup" in ti2.index.get("critical", [])


def test_remove_job_from_all_tags():
    ti = TagIndex(index={"nightly": ["backup", "report"], "critical": ["backup"]})
    ti2 = remove_job_tags(ti, "backup")
    assert "backup" not in ti2.index.get("nightly", [])
    assert "backup" not in ti2.index.get("critical", [])


def test_remove_job_drops_empty_tag():
    ti = TagIndex(index={"solo": ["only_job"]})
    ti2 = remove_job_tags(ti, "only_job")
    assert "solo" not in ti2.index


# --- query helpers ---

def test_jobs_for_tag_returns_correct_list():
    ti = TagIndex(index={"nightly": ["backup", "report"]})
    assert jobs_for_tag(ti, "nightly") == ["backup", "report"]


def test_jobs_for_missing_tag_returns_empty():
    ti = TagIndex()
    assert jobs_for_tag(ti, "nonexistent") == []


def test_tags_for_job_returns_all_tags():
    ti = TagIndex(index={"nightly": ["backup"], "critical": ["backup", "report"]})
    result = tags_for_job(ti, "backup")
    assert set(result) == {"nightly", "critical"}


def test_tags_for_unknown_job_returns_empty():
    ti = TagIndex(index={"nightly": ["backup"]})
    assert tags_for_job(ti, "ghost") == []
