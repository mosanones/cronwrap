"""Tests for cronwrap.timeout_policy."""
import pytest
from cronwrap.timeout_policy import TimeoutPolicy


def test_defaults_are_none():
    policy = TimeoutPolicy()
    assert policy.soft_timeout_seconds is None
    assert policy.hard_timeout_seconds is None
    assert policy.grace_period_seconds == 5.0


def test_soft_timeout_negative_raises():
    with pytest.raises(ValueError, match="soft_timeout_seconds must be positive"):
        TimeoutPolicy(soft_timeout_seconds=-1)


def test_hard_timeout_negative_raises():
    with pytest.raises(ValueError, match="hard_timeout_seconds must be positive"):
        TimeoutPolicy(hard_timeout_seconds=0)


def test_soft_must_be_less_than_hard():
    with pytest.raises(ValueError, match="soft_timeout_seconds must be less than"):
        TimeoutPolicy(soft_timeout_seconds=30, hard_timeout_seconds=10)


def test_soft_equal_to_hard_raises():
    with pytest.raises(ValueError, match="soft_timeout_seconds must be less than"):
        TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=10)


def test_grace_period_negative_raises():
    with pytest.raises(ValueError, match="grace_period_seconds must be non-negative"):
        TimeoutPolicy(grace_period_seconds=-1)


def test_effective_hard_timeout_explicit():
    policy = TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=30)
    assert policy.effective_hard_timeout() == 30


def test_effective_hard_timeout_derived_from_soft():
    policy = TimeoutPolicy(soft_timeout_seconds=20, grace_period_seconds=8)
    assert policy.effective_hard_timeout() == 28


def test_effective_hard_timeout_no_limits():
    policy = TimeoutPolicy()
    assert policy.effective_hard_timeout() is None


def test_classify_ok():
    policy = TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=30)
    assert policy.classify(5.0) == "ok"


def test_classify_soft_breach():
    policy = TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=30)
    assert policy.classify(15.0) == "soft_breach"


def test_classify_hard_breach():
    policy = TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=30)
    assert policy.classify(35.0) == "hard_breach"


def test_classify_exactly_at_soft_boundary():
    policy = TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=30)
    assert policy.classify(10.0) == "soft_breach"


def test_classify_no_policy_always_ok():
    policy = TimeoutPolicy()
    assert policy.classify(9999.0) == "ok"


def test_summary_no_policy():
    assert TimeoutPolicy().summary() == "no timeout policy"


def test_summary_soft_only():
    result = TimeoutPolicy(soft_timeout_seconds=15).summary()
    assert "soft=15" in result
    assert "grace=5" in result


def test_summary_both_limits():
    result = TimeoutPolicy(soft_timeout_seconds=10, hard_timeout_seconds=60).summary()
    assert "soft=10" in result
    assert "hard=60" in result


def test_summary_with_labels():
    result = TimeoutPolicy(soft_timeout_seconds=5, labels=["critical", "prod"]).summary()
    assert "critical,prod" in result
