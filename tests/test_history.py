"""Tests for cronwrap.history — run record persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.history import (
    MAX_HISTORY_ENTRIES,
    RunRecord,
    append_record,
    last_run,
    load_history,
    save_history,
)


@pytest.fixture()
def history_path(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _make_record(job_name: str = "nightly", success: bool = True, attempts: int = 1) -> RunRecord:
    return RunRecord(
        job_name=job_name,
        command="echo hello",
        started_at="2024-01-01T00:00:00+00:00",
        finished_at="2024-01-01T00:00:01+00:00",
        exit_code=0 if success else 1,
        duration_seconds=1.0,
        attempts=attempts,
        timed_out=False,
        success=success,
    )


def test_load_history_missing_file(history_path: Path) -> None:
    assert load_history(history_path) == []


def test_load_history_corrupt_file(history_path: Path) -> None:
    history_path.write_text("not json")
    assert load_history(history_path) == []


def test_save_and_load_roundtrip(history_path: Path) -> None:
    record = _make_record()
    save_history([record], history_path)
    loaded = load_history(history_path)
    assert len(loaded) == 1
    assert loaded[0] == record


def test_append_record_creates_file(history_path: Path) -> None:
    record = _make_record()
    append_record(record, history_path)
    assert history_path.exists()
    data = json.loads(history_path.read_text())
    assert len(data) == 1


def test_append_record_accumulates(history_path: Path) -> None:
    for i in range(3):
        append_record(_make_record(job_name=f"job_{i}"), history_path)
    records = load_history(history_path)
    assert len(records) == 3
    assert records[2].job_name == "job_2"


def test_history_trimmed_to_max(history_path: Path) -> None:
    records = [_make_record(job_name=f"job_{i}") for i in range(MAX_HISTORY_ENTRIES + 10)]
    save_history(records, history_path)
    loaded = load_history(history_path)
    assert len(loaded) == MAX_HISTORY_ENTRIES
    # Most recent entries are kept
    assert loaded[-1].job_name == f"job_{MAX_HISTORY_ENTRIES + 9}"


def test_last_run_returns_none_when_no_history(history_path: Path) -> None:
    assert last_run("missing", history_path) is None


def test_last_run_returns_most_recent(history_path: Path) -> None:
    append_record(_make_record(job_name="backup", success=False), history_path)
    append_record(_make_record(job_name="backup", success=True), history_path)
    result = last_run("backup", history_path)
    assert result is not None
    assert result.success is True


def test_last_run_filters_by_job_name(history_path: Path) -> None:
    append_record(_make_record(job_name="alpha"), history_path)
    append_record(_make_record(job_name="beta"), history_path)
    assert last_run("alpha", history_path) is not None
    assert last_run("gamma", history_path) is None
