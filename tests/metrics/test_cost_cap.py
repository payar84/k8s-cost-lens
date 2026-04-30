"""Tests for CostCapChecker."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_cap import CapViolation, CostCapChecker
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


def make_cost(namespace: str, hourly: float, monthly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_hourly=hourly / 2,
        memory_hourly=hourly / 2,
        total_hourly=hourly,
        total_monthly=monthly,
    )


@pytest.fixture
def checker() -> CostCapChecker:
    return CostCapChecker(
        hourly_caps={"prod": 1.0},
        monthly_caps={"prod": 500.0},
        default_hourly_cap=5.0,
        default_monthly_cap=2000.0,
    )


def test_no_violations_when_under_cap(checker):
    costs = [make_cost("prod", 0.5, 300.0)]
    assert checker.check(costs) == []


def test_hourly_cap_exceeded(checker):
    costs = [make_cost("prod", 2.0, 300.0)]
    violations = checker.check(costs)
    assert len(violations) == 1
    assert violations[0].namespace == "prod"
    assert violations[0].hourly_exceeded()
    assert not violations[0].monthly_exceeded()


def test_monthly_cap_exceeded(checker):
    costs = [make_cost("prod", 0.5, 600.0)]
    violations = checker.check(costs)
    assert len(violations) == 1
    assert violations[0].monthly_exceeded()
    assert not violations[0].hourly_exceeded()


def test_both_caps_exceeded(checker):
    costs = [make_cost("prod", 3.0, 700.0)]
    violations = checker.check(costs)
    assert len(violations) == 1
    v = violations[0]
    assert v.hourly_exceeded()
    assert v.monthly_exceeded()


def test_default_cap_applied_to_unknown_namespace(checker):
    costs = [make_cost("dev", 6.0, 100.0)]
    violations = checker.check(costs)
    assert len(violations) == 1
    assert violations[0].namespace == "dev"
    assert violations[0].hourly_exceeded()


def test_no_caps_returns_no_violations():
    empty_checker = CostCapChecker()
    costs = [make_cost("prod", 999.0, 999999.0)]
    assert empty_checker.check(costs) == []


def test_str_representation():
    v = CapViolation(
        namespace="staging",
        cap_hourly=1.0,
        cap_monthly=None,
        actual_hourly=2.5,
        actual_monthly=1800.0,
    )
    s = str(v)
    assert "staging" in s
    assert "hourly" in s
