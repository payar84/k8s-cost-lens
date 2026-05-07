"""Tests for CostTopNAnalyzer."""
import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_topn import CostTopNAnalyzer, TopNMetric


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(namespace=namespace, hourly_cost=hourly, monthly_cost=hourly * 720)


@pytest.fixture()
def sample_costs():
    return [
        make_cost("ns-a", 0.10),
        make_cost("ns-b", 0.50),
        make_cost("ns-c", 0.30),
        make_cost("ns-d", 0.05),
        make_cost("ns-e", 0.80),
    ]


def test_empty_costs_returns_empty():
    analyzer = CostTopNAnalyzer(n=3)
    assert analyzer.top([]) == []


def test_n_zero_raises():
    with pytest.raises(ValueError):
        CostTopNAnalyzer(n=0)


def test_top3_monthly_desc(sample_costs):
    analyzer = CostTopNAnalyzer(n=3, metric=TopNMetric.MONTHLY, ascending=False)
    results = analyzer.top(sample_costs)
    assert len(results) == 3
    assert results[0].namespace == "ns-e"
    assert results[1].namespace == "ns-b"
    assert results[2].namespace == "ns-c"


def test_top3_hourly_asc(sample_costs):
    analyzer = CostTopNAnalyzer(n=3, metric=TopNMetric.HOURLY, ascending=True)
    results = analyzer.top(sample_costs)
    assert results[0].namespace == "ns-d"
    assert results[1].namespace == "ns-a"
    assert results[2].namespace == "ns-c"


def test_ranks_are_sequential(sample_costs):
    analyzer = CostTopNAnalyzer(n=5)
    results = analyzer.top(sample_costs)
    assert [r.rank for r in results] == [1, 2, 3, 4, 5]


def test_n_larger_than_list_returns_all(sample_costs):
    analyzer = CostTopNAnalyzer(n=100)
    results = analyzer.top(sample_costs)
    assert len(results) == len(sample_costs)


def test_result_str_contains_namespace(sample_costs):
    analyzer = CostTopNAnalyzer(n=1)
    result = analyzer.top(sample_costs)[0]
    assert result.namespace in str(result)
    assert "#1" in str(result)


def test_monthly_cost_is_hourly_times_720(sample_costs):
    analyzer = CostTopNAnalyzer(n=5)
    results = analyzer.top(sample_costs)
    for r in results:
        assert abs(r.monthly_cost - r.hourly_cost * 720) < 1e-6
