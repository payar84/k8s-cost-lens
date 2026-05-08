"""Tests for CostEfficiencyAnalyzer."""
import pytest
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_efficiency import CostEfficiencyAnalyzer, EfficiencyScore


def make_cost(ns: str, cpu: float = 1.0, mem: float = 2.0) -> NamespaceCost:
    return NamespaceCost(
        namespace=ns,
        cpu_cores=cpu,
        memory_gb=mem,
        hourly_cost=cpu * 0.048 + mem * 0.006,
        monthly_cost=(cpu * 0.048 + mem * 0.006) * 720,
    )


@pytest.fixture
def analyzer() -> CostEfficiencyAnalyzer:
    return CostEfficiencyAnalyzer()


def test_empty_costs_returns_empty(analyzer):
    assert analyzer.score([], {}, {}) == []


def test_perfect_efficiency(analyzer):
    costs = [make_cost("ns-a", cpu=2.0, mem=4.0)]
    scores = analyzer.score(costs, {"ns-a": 2.0}, {"ns-a": 4.0})
    assert len(scores) == 1
    assert scores[0].cpu_efficiency == pytest.approx(1.0)
    assert scores[0].mem_efficiency == pytest.approx(1.0)
    assert scores[0].overall_efficiency == pytest.approx(1.0)


def test_zero_usage_gives_zero_efficiency(analyzer):
    costs = [make_cost("ns-b", cpu=1.0, mem=2.0)]
    scores = analyzer.score(costs, {"ns-b": 0.0}, {"ns-b": 0.0})
    assert scores[0].cpu_efficiency == pytest.approx(0.0)
    assert scores[0].mem_efficiency == pytest.approx(0.0)
    assert scores[0].overall_efficiency == pytest.approx(0.0)


def test_zero_requested_gives_none_efficiency(analyzer):
    costs = [make_cost("ns-c", cpu=0.0, mem=0.0)]
    scores = analyzer.score(costs, {"ns-c": 0.0}, {"ns-c": 0.0})
    assert scores[0].cpu_efficiency is None
    assert scores[0].mem_efficiency is None
    assert scores[0].overall_efficiency is None


def test_efficiency_capped_at_one(analyzer):
    costs = [make_cost("ns-d", cpu=1.0, mem=1.0)]
    # used > requested should be capped at 1.0
    scores = analyzer.score(costs, {"ns-d": 5.0}, {"ns-d": 5.0})
    assert scores[0].cpu_efficiency == pytest.approx(1.0)
    assert scores[0].mem_efficiency == pytest.approx(1.0)


def test_partial_efficiency(analyzer):
    costs = [make_cost("ns-e", cpu=4.0, mem=8.0)]
    scores = analyzer.score(costs, {"ns-e": 2.0}, {"ns-e": 4.0})
    assert scores[0].cpu_efficiency == pytest.approx(0.5)
    assert scores[0].mem_efficiency == pytest.approx(0.5)
    assert scores[0].overall_efficiency == pytest.approx(0.5)


def test_missing_namespace_in_used_defaults_to_zero(analyzer):
    costs = [make_cost("ns-f", cpu=1.0, mem=2.0)]
    scores = analyzer.score(costs, {}, {})
    assert scores[0].cpu_used == 0.0
    assert scores[0].mem_used_gb == 0.0


def test_str_representation(analyzer):
    costs = [make_cost("ns-g", cpu=2.0, mem=4.0)]
    scores = analyzer.score(costs, {"ns-g": 1.0}, {"ns-g": 2.0})
    assert "ns-g" in str(scores[0])
    assert "50.0%" in str(scores[0])
