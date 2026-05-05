"""Tests for cronwrap.metrics, cronwrap.metrics_hook, and cronwrap.metrics_reporter."""
from __future__ import annotations

import json
import os
import pytest

from cronwrap.metrics import (
    JobMetric,
    MetricsSummary,
    append_metric,
    load_metrics,
    save_metrics,
    summarise,
)
from cronwrap.metrics_hook import record_metric
from cronwrap.metrics_reporter import render_summary, render_single_summary
from cronwrap.executor import ExecutionResult


@pytest.fixture
def metrics_path(tmp_path):
    return str(tmp_path / "metrics.json")


def _metric(job="backup", success=True, duration=1.5, timed_out=False, attempt=1):
    return JobMetric(
        job_name=job,
        timestamp="2024-01-01T00:00:00",
        duration_seconds=duration,
        exit_code=0 if success else 1,
        attempt=attempt,
        timed_out=timed_out,
        success=success,
    )


def test_load_missing_file_returns_empty(metrics_path):
    assert load_metrics(metrics_path) == []


def test_load_corrupt_file_returns_empty(metrics_path):
    with open(metrics_path, "w") as fh:
        fh.write("not json{{")
    assert load_metrics(metrics_path) == []


def test_save_and_load_roundtrip(metrics_path):
    m = _metric()
    save_metrics(metrics_path, [m])
    loaded = load_metrics(metrics_path)
    assert len(loaded) == 1
    assert loaded[0].job_name == "backup"
    assert loaded[0].success is True


def test_append_metric_accumulates(metrics_path):
    append_metric(metrics_path, _metric(success=True))
    append_metric(metrics_path, _metric(success=False))
    loaded = load_metrics(metrics_path)
    assert len(loaded) == 2


def test_summarise_counts(metrics_path):
    metrics = [
        _metric(success=True, duration=2.0),
        _metric(success=True, duration=4.0),
        _metric(success=False, duration=1.0),
        _metric(job="other", success=True),
    ]
    summary = summarise("backup", metrics)
    assert summary.total_runs == 3
    assert summary.successful_runs == 2
    assert summary.failed_runs == 1
    assert summary.avg_duration_seconds == pytest.approx((2.0 + 4.0 + 1.0) / 3)
    assert summary.max_duration_seconds == pytest.approx(4.0)
    assert summary.min_duration_seconds == pytest.approx(1.0)


def test_summarise_no_runs_returns_zero_rate():
    summary = summarise("ghost", [])
    assert summary.success_rate == 0.0
    assert summary.total_runs == 0


def test_record_metric_from_execution_result(metrics_path):
    result = ExecutionResult(
        stdout="ok", stderr="", exit_code=0, timed_out=False, duration_seconds=0.42
    )
    metric = record_metric("myjob", result, attempt=2, metrics_path=metrics_path)
    assert metric.success is True
    assert metric.attempt == 2
    assert metric.duration_seconds == pytest.approx(0.42)
    loaded = load_metrics(metrics_path)
    assert len(loaded) == 1


def test_record_metric_timeout(metrics_path):
    result = ExecutionResult(
        stdout="", stderr="", exit_code=None, timed_out=True, duration_seconds=30.0
    )
    metric = record_metric("slow_job", result, metrics_path=metrics_path)
    assert metric.timed_out is True
    assert metric.success is False
    assert metric.exit_code == -1


def test_render_summary_contains_job_name():
    summary = MetricsSummary(job_name="cleanup")
    summary.ingest(_metric(job="cleanup", success=True, duration=5.0))
    output = render_summary(summary)
    assert "cleanup" in output
    assert "100.0%" in output


def test_render_single_summary_no_data(metrics_path):
    output = render_single_summary(metrics_path, "nonexistent")
    assert "No metrics" in output


def test_render_single_summary_with_data(metrics_path):
    append_metric(metrics_path, _metric(job="deploy", success=True, duration=3.0))
    output = render_single_summary(metrics_path, "deploy")
    assert "deploy" in output
    assert "3.000s" in output
