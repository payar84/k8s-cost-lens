"""Tests for CostTrendAnalyzer."""

import pytest

from k8s_cost_lens.metrics.aggregator import AggregatedMetrics
from k8s_cost_lens.metrics.cost_estimator import CostEstimator
from k8s_cost_lens.metrics.trend import CostTrendAnalyzer


CPU_PRICE = 0.048
MEM_PRICE = 0.006


@pytest.fixture
def analyzer() -> CostTrendAnalyzer:
    estimator = CostEstimator(cpu_price_per_core_hour=CPU_PRICE, memory_price_per_gb_hour=MEM_PRICE)
    return CostTrendAnalyzer(estimator)


def make_agg(namespace: str, cpu: float, memory_bytes: float) -> AggregatedMetrics:
    return AggregatedMetrics(
        namespace=namespace,
        avg_cpu_cores=cpu,
        avg_memory_bytes=memory_bytes,
        sample_count=1,
    )


def test_no_change_gives_zero_delta(analyzer):
    snap = [make_agg("default", 1.0, 1024 ** 3)]
    trends = analyzer.compare(snap, snap)
    assert len(trends) == 1
    assert trends[0].delta == pytest.approx(0.0)


def test_new_namespace_has_zero_previous_cost(analyzer):
    previous = []
    current = [make_agg("new-ns", 2.0, 0.0)]
    trends = analyzer.compare(previous, current)
    assert trends[0].previous_hourly_cost == pytest.approx(0.0)
    assert trends[0].current_hourly_cost == pytest.approx(2.0 * CPU_PRICE)


def test_percent_change_none_when_previous_zero(analyzer):
    trends = analyzer.compare([], [make_agg("ns", 1.0, 0.0)])
    assert trends[0].percent_change is None


def test_percent_change_increase(analyzer):
    prev = [make_agg("ns", 1.0, 0.0)]
    curr = [make_agg("ns", 2.0, 0.0)]
    trends = analyzer.compare(prev, curr)
    assert trends[0].percent_change == pytest.approx(100.0)


def test_results_sorted_by_namespace(analyzer):
    current = [
        make_agg("zebra", 1.0, 0.0),
        make_agg("alpha", 1.0, 0.0),
    ]
    trends = analyzer.compare(current, current)
    names = [t.namespace for t in trends]
    assert names == sorted(names)


def test_only_current_namespaces_returned(analyzer):
    previous = [make_agg("old-ns", 1.0, 0.0), make_agg("shared", 1.0, 0.0)]
    current = [make_agg("shared", 2.0, 0.0)]
    trends = analyzer.compare(previous, current)
    namespaces = {t.namespace for t in trends}
    assert namespaces == {"shared"}
