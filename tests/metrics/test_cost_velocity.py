"""Tests for CostVelocityAnalyzer."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_velocity import CostVelocityAnalyzer, VelocityResult


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(namespace=namespace, hourly_cost=hourly, monthly_cost=hourly * 720)


@pytest.fixture()
def analyzer() -> CostVelocityAnalyzer:
    return CostVelocityAnalyzer()


# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------

def test_no_snapshots_returns_empty(analyzer):
    assert analyzer.analyze() == []


def test_single_snapshot_returns_empty(analyzer):
    analyzer.add_snapshot([make_cost("default", 0.5)])
    assert analyzer.analyze() == []


def test_two_identical_snapshots_are_stable(analyzer):
    snap = [make_cost("default", 1.0)]
    analyzer.add_snapshot(snap)
    analyzer.add_snapshot(snap)
    results = analyzer.analyze()
    assert len(results) == 1
    assert results[0].direction == "stable"
    assert abs(results[0].hourly_velocity) < 1e-9


def test_increasing_cost_is_rising(analyzer):
    for i in range(1, 6):
        analyzer.add_snapshot([make_cost("web", float(i))])
    results = analyzer.analyze()
    assert len(results) == 1
    r = results[0]
    assert r.direction == "rising"
    assert r.hourly_velocity > 0


def test_decreasing_cost_is_falling(analyzer):
    for i in range(5, 0, -1):
        analyzer.add_snapshot([make_cost("web", float(i))])
    results = analyzer.analyze()
    assert results[0].direction == "falling"
    assert results[0].hourly_velocity < 0


def test_monthly_velocity_is_720_times_hourly(analyzer):
    for v in [1.0, 2.0, 3.0]:
        analyzer.add_snapshot([make_cost("ns", v)])
    results = analyzer.analyze()
    r = results[0]
    assert abs(r.monthly_velocity - r.hourly_velocity * 720) < 1e-9


def test_multiple_namespaces_analysed_independently():
    a = CostVelocityAnalyzer()
    a.add_snapshot([make_cost("rising", 1.0), make_cost("falling", 5.0)])
    a.add_snapshot([make_cost("rising", 2.0), make_cost("falling", 4.0)])
    a.add_snapshot([make_cost("rising", 3.0), make_cost("falling", 3.0)])
    results = {r.namespace: r for r in a.analyze()}
    assert results["rising"].direction == "rising"
    assert results["falling"].direction == "falling"


def test_namespace_missing_from_some_snapshots_still_computed():
    """A namespace that only appears in later snapshots should still be analysed."""
    a = CostVelocityAnalyzer()
    a.add_snapshot([make_cost("old", 1.0)])
    a.add_snapshot([make_cost("old", 2.0), make_cost("new", 0.5)])
    results = {r.namespace: r for r in a.analyze()}
    # 'new' only has one data-point → velocity == 0 → stable
    assert results["new"].direction == "stable"
    assert results["old"].direction == "rising"


def test_str_representation():
    r = VelocityResult(namespace="prod", hourly_velocity=0.001, monthly_velocity=0.72, direction="rising")
    s = str(r)
    assert "prod" in s
    assert "rising" in s
