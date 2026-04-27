"""Tests for CostThresholdChecker."""
from __future__ import annotations

from typing import List

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.threshold import CostThresholdChecker, ThresholdViolation


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_hourly=hourly * 0.6,
        memory_hourly=hourly * 0.4,
    )


@pytest.fixture
def checker() -> CostThresholdChecker:
    return CostThresholdChecker()


def test_no_limits_returns_no_violations(checker: CostThresholdChecker) -> None:
    costs = [make_cost("default", 1.0), make_cost("kube-system", 0.5)]
    assert checker.check(costs) == []


def test_global_hourly_limit_triggers_violation(checker: CostThresholdChecker) -> None:
    checker.global_hourly_limit = 0.5
    costs = [make_cost("default", 1.0), make_cost("cheap", 0.1)]
    violations = checker.check(costs)
    assert len(violations) == 1
    assert violations[0].namespace == "default"
    assert violations[0].exceeded_hourly


def test_global_monthly_limit_triggers_violation(checker: CostThresholdChecker) -> None:
    checker.global_monthly_limit = 100.0
    costs = [make_cost("default", 1.0)]  # monthly = 1.0 * 720 = 720
    violations = checker.check(costs)
    assert len(violations) == 1
    assert violations[0].exceeded_monthly
    assert not violations[0].exceeded_hourly


def test_namespace_limit_overrides_global(checker: CostThresholdChecker) -> None:
    checker.global_hourly_limit = 0.1
    checker.set_namespace_limit("exempt", hourly=999.0)
    costs = [make_cost("exempt", 5.0), make_cost("other", 5.0)]
    violations = checker.check(costs)
    namespaces = {v.namespace for v in violations}
    assert "exempt" not in namespaces
    assert "other" in namespaces


def test_violation_str_contains_namespace() -> None:
    v = ThresholdViolation(
        namespace="production",
        hourly_cost=2.0,
        monthly_cost=1440.0,
        hourly_limit=1.0,
        monthly_limit=500.0,
    )
    text = str(v)
    assert "production" in text
    assert "hourly" in text
    assert "monthly" in text


def test_exact_limit_not_a_violation(checker: CostThresholdChecker) -> None:
    checker.global_hourly_limit = 1.0
    costs = [make_cost("default", 1.0)]
    # hourly_cost == limit should NOT be a violation (strictly greater)
    violations = checker.check(costs)
    assert violations == []


def test_multiple_violations_returned(checker: CostThresholdChecker) -> None:
    checker.global_monthly_limit = 50.0
    costs = [
        make_cost("ns-a", 0.5),  # monthly ~360
        make_cost("ns-b", 0.5),
        make_cost("ns-c", 0.01),  # monthly ~7.2 — under limit
    ]
    violations = checker.check(costs)
    assert len(violations) == 2
