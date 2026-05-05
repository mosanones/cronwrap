"""Tests for cronwrap.schedule_store persistence helpers."""

import json
import pytest
from pathlib import Path

from cronwrap.schedule_store import (
    ScheduleEntry,
    get_due_jobs,
    load_store,
    save_store,
    upsert_entry,
)


@pytest.fixture()
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "schedule.json"


# ---------------------------------------------------------------------------
# load_store
# ---------------------------------------------------------------------------

def test_load_missing_file_returns_empty(store_path):
    assert load_store(store_path) == {}


def test_load_corrupt_file_returns_empty(store_path):
    store_path.write_text("not json")
    assert load_store(store_path) == {}


# ---------------------------------------------------------------------------
# save_store / load_store round-trip
# ---------------------------------------------------------------------------

def test_roundtrip(store_path):
    entry = ScheduleEntry(
        job_name="backup",
        cron_expression="0 2 * * *",
        enabled=True,
        last_run="2024-01-01T02:00:00",
        next_run="2024-01-02T02:00:00",
    )
    save_store({"backup": entry}, store_path)
    loaded = load_store(store_path)
    assert "backup" in loaded
    assert loaded["backup"].cron_expression == "0 2 * * *"
    assert loaded["backup"].enabled is True


# ---------------------------------------------------------------------------
# upsert_entry
# ---------------------------------------------------------------------------

def test_upsert_creates_new(store_path):
    entry = ScheduleEntry(job_name="sync", cron_expression="*/5 * * * *")
    upsert_entry(entry, store_path)
    loaded = load_store(store_path)
    assert "sync" in loaded


def test_upsert_overwrites_existing(store_path):
    e1 = ScheduleEntry(job_name="sync", cron_expression="*/5 * * * *", enabled=True)
    e2 = ScheduleEntry(job_name="sync", cron_expression="*/10 * * * *", enabled=False)
    upsert_entry(e1, store_path)
    upsert_entry(e2, store_path)
    loaded = load_store(store_path)
    assert loaded["sync"].cron_expression == "*/10 * * * *"
    assert loaded["sync"].enabled is False


# ---------------------------------------------------------------------------
# get_due_jobs
# ---------------------------------------------------------------------------

def test_due_jobs_returns_overdue(store_path):
    entries = {
        "a": ScheduleEntry("a", "* * * * *", enabled=True, next_run="2024-01-01T00:00:00"),
        "b": ScheduleEntry("b", "* * * * *", enabled=True, next_run="2099-01-01T00:00:00"),
    }
    due = get_due_jobs(entries, now_iso="2024-06-01T12:00:00")
    assert len(due) == 1
    assert due[0].job_name == "a"


def test_due_jobs_skips_disabled(store_path):
    entries = {
        "x": ScheduleEntry("x", "* * * * *", enabled=False, next_run="2000-01-01T00:00:00"),
    }
    due = get_due_jobs(entries, now_iso="2024-06-01T12:00:00")
    assert due == []


def test_due_jobs_includes_none_next_run():
    entries = {
        "y": ScheduleEntry("y", "* * * * *", enabled=True, next_run=None),
    }
    due = get_due_jobs(entries, now_iso="2024-06-01T12:00:00")
    assert len(due) == 1
