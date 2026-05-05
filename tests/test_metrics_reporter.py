"""Additional tests focused on metrics_reporter rendering edge cases."""
from __future__ import annotations

import pytest

from cronwrap.metrics import JobMetric, MetricsSummary, save_metrics
from cronwrap.metrics_reporter import render_all_summaries, render_summary, _bar


def _make_metric(job="job", success=True, duration=1.0, timed_out=False):
    return JobMetric(
        job_name=job,
        timestamp="2024-06-01T12:00:00",
        duration_seconds=duration,
        exit_code=0 if success else 2,
        attempt=1,
        timed_out=timed_out,
        success=success,
    )


def test_bar_full():
    assert _bar(1.0) == "[####################]"


def test_bar_empty():
    assert _bar(0.0) == "[--------------------]"


def test_bar_half():
    result = _bar(0.5)
    assert result.count("#") == 10
    assert result.count("-") == 10


def test_render_summary_shows_all_fields():
    summary = MetricsSummary(job_name="etl")
    summary.ingest(_make_metric(job="etl", success=True, duration=2.5))
    summary.ingest(_make_metric(job="etl", success=False, duration=0.5))
    output = render_summary(summary)
    assert "Total runs      : 2" in output
    assert "Successful      : 1" in output
    assert "Failed          : 1" in output
    assert "50.0%" in output
    assert "Avg duration" in output


def test_render_all_summaries_empty_file(tmp_path):
    path = str(tmp_path / "metrics.json")
    output = render_all_summaries(path, ["job_a", "job_b"])
    assert "No metrics" in output


def test_render_all_summaries_filters_by_name(tmp_path):
    path = str(tmp_path / "metrics.json")
    metrics = [
        _make_metric(job="alpha", success=True),
        _make_metric(job="beta", success=False),
    ]
    save_metrics(path, metrics)
    output = render_all_summaries(path, ["alpha"])
    assert "alpha" in output
    assert "beta" not in output


def test_render_all_summaries_no_matching_jobs(tmp_path):
    path = str(tmp_path / "metrics.json")
    save_metrics(path, [_make_metric(job="alpha")])
    output = render_all_summaries(path, ["gamma"])
    assert "No metrics found" in output


def test_render_all_summaries_multiple_jobs(tmp_path):
    path = str(tmp_path / "metrics.json")
    metrics = [
        _make_metric(job="alpha", success=True, duration=1.0),
        _make_metric(job="beta", success=True, duration=2.0),
    ]
    save_metrics(path, metrics)
    output = render_all_summaries(path, ["alpha", "beta"])
    assert "alpha" in output
    assert "beta" in output
