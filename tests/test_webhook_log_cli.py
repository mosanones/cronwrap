"""Tests for cronwrap.webhook_log_cli."""
from __future__ import annotations

import json

import pytest

from cronwrap.webhook_log import WebhookLogConfig
from cronwrap.webhook_log_cli import render_payload_preview, render_config

_RECORD = {
    "job_name": "nightly",
    "status": "failure",
    "exit_code": 1,
    "duration": 0.5,
    "started_at": "2024-06-01T02:00:00",
    "finished_at": "2024-06-01T02:00:00",
    "stdout": "output here",
    "stderr": "error here",
}


def test_render_payload_preview_is_valid_json():
    preview = render_payload_preview(_RECORD)
    parsed = json.loads(preview)
    assert parsed["job"] == "nightly"
    assert parsed["status"] == "failure"


def test_render_payload_preview_excludes_output_by_default():
    preview = render_payload_preview(_RECORD, include_output=False)
    parsed = json.loads(preview)
    assert "stdout" not in parsed


def test_render_payload_preview_includes_output_when_requested():
    preview = render_payload_preview(_RECORD, include_output=True)
    parsed = json.loads(preview)
    assert parsed["stdout"] == "output here"


def test_render_config_shows_url():
    cfg = WebhookLogConfig(url="https://logs.example.com/ingest", timeout=30)
    out = render_config(cfg)
    assert "https://logs.example.com/ingest" in out
    assert "30" in out


def test_render_config_no_headers():
    cfg = WebhookLogConfig(url="https://x.com")
    out = render_config(cfg)
    assert "(none)" in out


def test_render_config_with_headers():
    cfg = WebhookLogConfig(
        url="https://x.com",
        headers={"Authorization": "Bearer tok", "X-Source": "cronwrap"},
    )
    out = render_config(cfg)
    assert "Authorization" in out
    assert "Bearer tok" in out
    assert "X-Source" in out
