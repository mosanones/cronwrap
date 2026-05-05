"""Tests for cronwrap.scheduler (CronExpression parsing and next_run)."""

import pytest
from datetime import datetime

from cronwrap.scheduler import CronExpression, _parse_field


# ---------------------------------------------------------------------------
# _parse_field
# ---------------------------------------------------------------------------

def test_parse_star():
    assert _parse_field("*", 0, 4) == [0, 1, 2, 3, 4]


def test_parse_single_value():
    assert _parse_field("3", 0, 59) == [3]


def test_parse_range():
    assert _parse_field("1-3", 0, 59) == [1, 2, 3]


def test_parse_step():
    assert _parse_field("*/15", 0, 59) == [0, 15, 30, 45]


def test_parse_list():
    assert _parse_field("1,3,5", 0, 59) == [1, 3, 5]


def test_parse_out_of_range_raises():
    with pytest.raises(ValueError, match="out of range"):
        _parse_field("60", 0, 59)


# ---------------------------------------------------------------------------
# CronExpression.parse
# ---------------------------------------------------------------------------

def test_parse_wrong_field_count():
    with pytest.raises(ValueError, match="5 cron fields"):
        CronExpression.parse("* * * *")


def test_parse_every_minute():
    expr = CronExpression.parse("* * * * *")
    assert len(expr.minute) == 60
    assert len(expr.hour) == 24


def test_parse_specific():
    expr = CronExpression.parse("30 6 * * 1")
    assert expr.minute == [30]
    assert expr.hour == [6]
    assert expr.weekday == [1]


# ---------------------------------------------------------------------------
# CronExpression.matches
# ---------------------------------------------------------------------------

def test_matches_true():
    expr = CronExpression.parse("30 6 * * *")
    dt = datetime(2024, 3, 15, 6, 30)
    assert expr.matches(dt) is True


def test_matches_false():
    expr = CronExpression.parse("30 6 * * *")
    dt = datetime(2024, 3, 15, 6, 31)
    assert expr.matches(dt) is False


# ---------------------------------------------------------------------------
# CronExpression.next_run
# ---------------------------------------------------------------------------

def test_next_run_advances_one_minute():
    expr = CronExpression.parse("* * * * *")
    base = datetime(2024, 1, 1, 0, 0)
    nxt = expr.next_run(after=base)
    assert nxt == datetime(2024, 1, 1, 0, 1)


def test_next_run_specific_hour():
    expr = CronExpression.parse("0 9 * * *")
    base = datetime(2024, 6, 1, 9, 0)   # already at 09:00 — should give next day
    nxt = expr.next_run(after=base)
    assert nxt == datetime(2024, 6, 2, 9, 0)
