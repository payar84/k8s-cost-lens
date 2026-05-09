"""Tests for CostPercentileAnalyzer and PercentileResult."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_percentile import (
    CostPercentileAnalyzer,
    PercentileResult,
    _percentile_rank,
)


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=hourly * 0.6,
        memory_cost=hourly * 0.4,
    )


@pytest.fixture()
def analyzer() -> CostPercentileAnalyzer:
    return CostPercentileAnalyzer()


# ---------------------------------------------------------------------------
# _percentile_rank helpers
# ---------------------------------------------------------------------------

def test_percentile_rank_empty_returns_zero():
    assert _percentile_rank(5.0, []) == 0.0


def test_percentile_rank_single_value_is_50():
    assert _percentile_rank(1.0, [1.0]) == 50.0


def test_percentile_rank_lowest_is_below_50():
    values = [1.0, 2.0, 3.0, 4.0]
    rank = _percentile_rank(1.0, values)
    assert rank < 50.0


def test_percentile_rank_highest_is_above_50():
    values = [1.0, 2.0, 3.0, 4.0]
    rank = _percentile_rank(4.0, values)
    assert rank > 50.0


# ---------------------------------------------------------------------------
# CostPercentileAnalyzer
# ---------------------------------------------------------------------------

def test_empty_costs_returns_empty(analyzer):
    assert analyzer.analyze([]) == []


def test_single_namespace_has_50th_percentile(analyzer):
    costs = [make_cost("default", 0.10)]
    results = analyzer.analyze(costs)
    assert len(results) == 1
    assert results[0].hourly_percentile == pytest.approx(50.0)
    assert results[0].monthly_percentile == pytest.approx(50.0)


def test_result_count_matches_input(analyzer):
    costs = [make_cost(f"ns-{i}", float(i)) for i in range(1, 6)]
    results = analyzer.analyze(costs)
    assert len(results) == 5


def test_namespace_names_preserved(analyzer):
    costs = [make_cost("alpha", 0.05), make_cost("beta", 0.10)]
    results = analyzer.analyze(costs)
    names = {r.namespace for r in results}
    assert names == {"alpha", "beta"}


def test_higher_cost_has_higher_percentile(analyzer):
    costs = [make_cost("cheap", 0.01), make_cost("expensive", 1.00)]
    results = analyzer.analyze(costs)
    by_ns = {r.namespace: r for r in results}
    assert by_ns["expensive"].monthly_percentile > by_ns["cheap"].monthly_percentile


def test_str_representation_contains_namespace():
    r = PercentileResult(
        namespace="kube-system",
        hourly_cost=0.05,
        monthly_cost=36.0,
        hourly_percentile=75.0,
        monthly_percentile=75.0,
    )
    assert "kube-system" in str(r)
    assert "p75.0" in str(r)
