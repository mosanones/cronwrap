"""Tests for cronwrap.snapshot_cli rendering helpers."""
from __future__ import annotations

import pytest

from cronwrap.snapshot import JobSnapshot, save_snapshot
from cronwrap.snapshot_cli import (
    render_snapshot,
    render_all_snapshots,
    render_flapping_jobs,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path / "snapshots")


def _snap(job_name="backup", status="success", exit_code=0, failures=0):
    return JobSnapshot(
        job_name=job_name,
        last_exit_code=exit_code,
        last_status=status,
        last_run_at="2024-06-01T12:00:00",
        consecutive_failures=failures,
        last_duration_seconds=2.5,
    )


def test_render_snapshot_success_icon(store):
    out = render_snapshot(_snap(status="success"))
    assert "✅" in out
    assert "success" in out


def test_render_snapshot_failure_icon(store):
    out = render_snapshot(_snap(status="failure", exit_code=1))
    assert "❌" in out


def test_render_snapshot_timeout_icon(store):
    out = render_snapshot(_snap(status="timeout", exit_code=1))
    assert "⏱️" in out


def test_render_snapshot_includes_duration(store):
    out = render_snapshot(_snap())
    assert "2.50s" in out


def test_render_snapshot_includes_consecutive(store):
    out = render_snapshot(_snap(failures=3))
    assert "3" in out


def test_render_all_snapshots_empty_dir(store):
    out = render_all_snapshots(store)
    assert "no snapshots" in out


def test_render_all_snapshots_missing_dir(tmp_path):
    out = render_all_snapshots(str(tmp_path / "nonexistent"))
    assert "no snapshots" in out


def test_render_all_snapshots_lists_jobs(store):
    save_snapshot(store, _snap("job_a"))
    save_snapshot(store, _snap("job_b", status="failure", exit_code=1, failures=1))
    out = render_all_snapshots(store)
    assert "job_a" in out
    assert "job_b" in out


def test_render_flapping_no_flapping(store):
    save_snapshot(store, _snap("clean", failures=0))
    out = render_flapping_jobs(store, threshold=2)
    assert "none" in out


def test_render_flapping_shows_bad_jobs(store):
    save_snapshot(store, _snap("bad_job", status="failure", exit_code=1, failures=3))
    out = render_flapping_jobs(store, threshold=2)
    assert "bad_job" in out
    assert "3" in out


def test_render_flapping_missing_dir(tmp_path):
    out = render_flapping_jobs(str(tmp_path / "none"), threshold=1)
    assert "no snapshots" in out
