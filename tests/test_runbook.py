"""Tests for runbook module, CLI helpers, and hook."""
from __future__ import annotations

import pytest
from pathlib import Path

from cronwrap.runbook import (
    set_runbook, get_runbook, remove_runbook,
    load_runbook_index, save_runbook_index, RunbookEntry,
)
from cronwrap.runbook_cli import render_runbook, render_all_runbooks, render_runbook_search
from cronwrap.runbook_hook import attach_runbook_to_record, runbook_summary


@pytest.fixture()
def store(tmp_path: Path) -> str:
    return str(tmp_path)


# ── runbook core ─────────────────────────────────────────────────────────────

def test_load_missing_file_returns_empty(store):
    assert load_runbook_index(store) == {}


def test_load_corrupt_file_returns_empty(store):
    (Path(store) / "runbooks.json").write_text("not json")
    assert load_runbook_index(store) == {}


def test_set_and_get_runbook(store):
    entry = set_runbook(store, "backup", url="https://wiki/backup", notes="nightly")
    assert entry.job_name == "backup"
    fetched = get_runbook(store, "backup")
    assert fetched is not None
    assert fetched.url == "https://wiki/backup"
    assert fetched.notes == "nightly"


def test_get_missing_returns_none(store):
    assert get_runbook(store, "ghost") is None


def test_remove_existing_returns_true(store):
    set_runbook(store, "job1")
    assert remove_runbook(store, "job1") is True
    assert get_runbook(store, "job1") is None


def test_remove_missing_returns_false(store):
    assert remove_runbook(store, "ghost") is False


def test_roundtrip_with_tags(store):
    set_runbook(store, "etl", tags=["data", "critical"])
    entry = get_runbook(store, "etl")
    assert "data" in entry.tags
    assert "critical" in entry.tags


# ── CLI rendering ─────────────────────────────────────────────────────────────

def test_render_runbook_shows_url(store):
    entry = RunbookEntry(job_name="j", url="https://x", notes="hi", tags=["t"])
    out = render_runbook(entry)
    assert "https://x" in out
    assert "hi" in out
    assert "t" in out


def test_render_all_runbooks_empty(store):
    assert "No runbook" in render_all_runbooks(store)


def test_render_all_runbooks_lists_jobs(store):
    set_runbook(store, "alpha", url="https://a")
    set_runbook(store, "beta", url="https://b")
    out = render_all_runbooks(store)
    assert "alpha" in out
    assert "beta" in out


def test_render_search_by_tag(store):
    set_runbook(store, "tagged", tags=["ops"])
    set_runbook(store, "other", tags=["dev"])
    out = render_runbook_search(store, tag="ops")
    assert "tagged" in out
    assert "other" not in out


def test_render_search_url_only(store):
    set_runbook(store, "with_url", url="https://docs")
    set_runbook(store, "no_url")
    out = render_runbook_search(store, url_only=True)
    assert "with_url" in out
    assert "no_url" not in out


# ── hook ──────────────────────────────────────────────────────────────────────

def test_attach_runbook_to_record(store):
    set_runbook(store, "myjob", url="https://rb", notes="see this")
    record: dict = {}
    attach_runbook_to_record(record, "myjob", store_dir=store)
    assert record["runbook"]["url"] == "https://rb"


def test_attach_runbook_missing_job_no_key(store):
    record: dict = {}
    attach_runbook_to_record(record, "ghost", store_dir=store)
    assert "runbook" not in record


def test_runbook_summary_with_url(store):
    set_runbook(store, "j", url="https://wiki", notes="short note")
    s = runbook_summary("j", store_dir=store)
    assert "https://wiki" in s


def test_runbook_summary_missing_job_empty_string(store):
    assert runbook_summary("ghost", store_dir=store) == ""
