"""Tests for cronwrap.cost, cost_hook, and cost_cli."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch

from cronwrap.cost import (
    CostEntry, load_cost_log, save_cost_log,
    append_cost_entry, job_total_cost, all_job_totals,
)
from cronwrap.cost_hook import record_cost
from cronwrap.cost_cli import render_job_cost_report, render_all_costs, render_cost_breakdown
from cronwrap.executor import ExecutionResult


@pytest.fixture
def store(tmp_path):
    return str(tmp_path)


def _entry(job="backup", duration=10.0, rate=0.00001, ts="2024-01-01T00:00:00"):
    return CostEntry(job_name=job, timestamp=ts, duration_seconds=duration, cost_per_second=rate)


def test_load_missing_file_returns_empty(store):
    assert load_cost_log(store) == []


def test_load_corrupt_file_returns_empty(store):
    Path(store, "cost_log.json").write_text("not json")
    assert load_cost_log(store) == []


def test_save_and_load_roundtrip(store):
    entries = [_entry("job_a"), _entry("job_b", duration=5.0)]
    save_cost_log(store, entries)
    loaded = load_cost_log(store)
    assert len(loaded) == 2
    assert loaded[0].job_name == "job_a"
    assert loaded[1].duration_seconds == 5.0


def test_total_cost_calculation():
    e = _entry(duration=100.0, rate=0.00001)
    assert e.total_cost == pytest.approx(0.001, rel=1e-6)


def test_append_cost_entry(store):
    append_cost_entry(store, _entry("nightly"))
    append_cost_entry(store, _entry("nightly", duration=20.0))
    entries = load_cost_log(store)
    assert len(entries) == 2


def test_job_total_cost(store):
    append_cost_entry(store, _entry("backup", duration=10.0, rate=0.00001))
    append_cost_entry(store, _entry("backup", duration=20.0, rate=0.00001))
    total = job_total_cost(store, "backup")
    assert total == pytest.approx(0.0003, rel=1e-6)


def test_all_job_totals(store):
    append_cost_entry(store, _entry("alpha", duration=10.0, rate=0.00001))
    append_cost_entry(store, _entry("beta", duration=50.0, rate=0.00001))
    totals = all_job_totals(store)
    assert "alpha" in totals
    assert "beta" in totals
    assert totals["beta"] > totals["alpha"]


def test_record_cost_hook(store):
    result = ExecutionResult(
        returncode=0, stdout="", stderr="",
        duration=30.0, timed_out=False, started_at="2024-06-01T12:00:00"
    )
    record_cost("myjob", result, store, cost_per_second=0.00002)
    entries = load_cost_log(store)
    assert len(entries) == 1
    assert entries[0].job_name == "myjob"
    assert entries[0].total_cost == pytest.approx(0.0006, rel=1e-6)


def test_record_cost_skips_none_duration(store):
    result = ExecutionResult(
        returncode=1, stdout="", stderr="",
        duration=None, timed_out=False, started_at="2024-06-01T12:00:00"
    )
    record_cost("myjob", result, store)
    assert load_cost_log(store) == []


def test_record_cost_reads_env_rate(store, monkeypatch):
    monkeypatch.setenv("CRONWRAP_COST_PER_SECOND", "0.00005")
    result = ExecutionResult(
        returncode=0, stdout="", stderr="",
        duration=10.0, timed_out=False, started_at="2024-06-01T12:00:00"
    )
    record_cost("envjob", result, store)
    entries = load_cost_log(store)
    assert entries[0].cost_per_second == pytest.approx(0.00005)


def test_render_job_cost_report_no_data(store):
    out = render_job_cost_report(store, "ghost")
    assert "No cost data" in out


def test_render_job_cost_report_with_data(store):
    append_cost_entry(store, _entry("nightly", duration=60.0, rate=0.00001))
    out = render_job_cost_report(store, "nightly")
    assert "nightly" in out
    assert "Total" in out


def test_render_all_costs_empty(store):
    assert "No cost data" in render_all_costs(store)


def test_render_all_costs_with_data(store):
    append_cost_entry(store, _entry("alpha"))
    append_cost_entry(store, _entry("beta"))
    out = render_all_costs(store)
    assert "alpha" in out
    assert "Grand total" in out


def test_render_cost_breakdown(store):
    for i in range(6):
        append_cost_entry(store, _entry("daily", duration=float(i + 1)))
    out = render_cost_breakdown(store, "daily", top_n=3)
    assert "Top 3" in out
    assert "daily" in out
