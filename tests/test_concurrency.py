"""Tests for cronwrap.concurrency."""
from __future__ import annotations

import json
import pytest

from cronwrap.concurrency import (
    ConcurrencyConfig,
    ConcurrencyLimitExceeded,
    acquire_slot,
    active_slots,
    release_slot,
)


@pytest.fixture()
def cfg(tmp_path):
    return ConcurrencyConfig(max_concurrent=2, state_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_config_valid():
    cfg = ConcurrencyConfig(max_concurrent=3)
    assert cfg.max_concurrent == 3


def test_config_zero_raises():
    with pytest.raises(ValueError, match="max_concurrent"):
        ConcurrencyConfig(max_concurrent=0)


def test_config_negative_raises():
    with pytest.raises(ValueError):
        ConcurrencyConfig(max_concurrent=-1)


# ---------------------------------------------------------------------------
# Slot lifecycle
# ---------------------------------------------------------------------------

def test_acquire_creates_slot(cfg):
    acquire_slot("backup", cfg, run_id="run-1")
    slots = active_slots("backup", cfg)
    assert len(slots) == 1
    assert slots[0]["run_id"] == "run-1"


def test_release_removes_slot(cfg):
    acquire_slot("backup", cfg, run_id="run-1")
    release_slot("backup", cfg, run_id="run-1")
    assert active_slots("backup", cfg) == []


def test_multiple_slots_within_limit(cfg):
    acquire_slot("backup", cfg, run_id="run-1")
    acquire_slot("backup", cfg, run_id="run-2")
    assert len(active_slots("backup", cfg)) == 2


def test_exceeding_limit_raises(cfg):
    acquire_slot("backup", cfg, run_id="run-1")
    acquire_slot("backup", cfg, run_id="run-2")
    with pytest.raises(ConcurrencyLimitExceeded, match="backup"):
        acquire_slot("backup", cfg, run_id="run-3")


def test_release_only_removes_matching_run_id(cfg):
    acquire_slot("backup", cfg, run_id="run-1")
    acquire_slot("backup", cfg, run_id="run-2")
    release_slot("backup", cfg, run_id="run-1")
    slots = active_slots("backup", cfg)
    assert len(slots) == 1
    assert slots[0]["run_id"] == "run-2"


def test_release_unknown_run_id_is_noop(cfg):
    acquire_slot("backup", cfg, run_id="run-1")
    release_slot("backup", cfg, run_id="nonexistent")
    assert len(active_slots("backup", cfg)) == 1


def test_active_slots_missing_file_returns_empty(cfg):
    assert active_slots("no-such-job", cfg) == []


def test_corrupt_state_file_treated_as_empty(cfg, tmp_path):
    state_file = tmp_path / "backup.concurrency.json"
    state_file.write_text("not valid json")
    # Should not raise; corrupt file treated as empty
    acquire_slot("backup", cfg, run_id="run-1")
    assert len(active_slots("backup", cfg)) == 1


def test_slot_limit_one_enforced():
    import tempfile, os
    with tempfile.TemporaryDirectory() as d:
        strict = ConcurrencyConfig(max_concurrent=1, state_dir=d)
        acquire_slot("etl", strict, run_id="r1")
        with pytest.raises(ConcurrencyLimitExceeded):
            acquire_slot("etl", strict, run_id="r2")
        release_slot("etl", strict, run_id="r1")
        # After release, a new slot should be acquirable
        acquire_slot("etl", strict, run_id="r2")
        assert len(active_slots("etl", strict)) == 1
