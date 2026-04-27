"""Tests for MetricsAggregator."""

import pytest

from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.aggregator import MetricsAggregator


def make_nm(namespace: str, cpu: float, memory: float) -> NamespaceMetrics:
    return NamespaceMetrics(namespace=namespace, cpu_cores=cpu, memory_bytes=memory)


@pytest.fixture
def aggregator() -> MetricsAggregator:
    return MetricsAggregator()


def test_empty_aggregate_returns_empty_list(aggregator):
    assert aggregator.aggregate() == []


def test_single_snapshot_returns_same_values(aggregator):
    aggregator.add_snapshot([make_nm("default", 1.0, 512.0)])
    results = aggregator.aggregate()
    assert len(results) == 1
    assert results[0].namespace == "default"
    assert results[0].avg_cpu_cores == pytest.approx(1.0)
    assert results[0].avg_memory_bytes == pytest.approx(512.0)
    assert results[0].sample_count == 1


def test_multiple_snapshots_are_averaged(aggregator):
    aggregator.add_snapshot([make_nm("default", 1.0, 200.0)])
    aggregator.add_snapshot([make_nm("default", 3.0, 400.0)])
    results = aggregator.aggregate()
    assert results[0].avg_cpu_cores == pytest.approx(2.0)
    assert results[0].avg_memory_bytes == pytest.approx(300.0)
    assert results[0].sample_count == 2


def test_multiple_namespaces_tracked_independently(aggregator):
    aggregator.add_snapshot([
        make_nm("alpha", 2.0, 100.0),
        make_nm("beta", 4.0, 200.0),
    ])
    results = {r.namespace: r for r in aggregator.aggregate()}
    assert results["alpha"].avg_cpu_cores == pytest.approx(2.0)
    assert results["beta"].avg_cpu_cores == pytest.approx(4.0)


def test_results_are_sorted_by_namespace(aggregator):
    aggregator.add_snapshot([
        make_nm("zebra", 1.0, 1.0),
        make_nm("apple", 1.0, 1.0),
        make_nm("mango", 1.0, 1.0),
    ])
    names = [r.namespace for r in aggregator.aggregate()]
    assert names == sorted(names)


def test_namespace_count(aggregator):
    aggregator.add_snapshot([make_nm("ns1", 1.0, 1.0), make_nm("ns2", 1.0, 1.0)])
    assert aggregator.namespace_count == 2


def test_clear_resets_state(aggregator):
    aggregator.add_snapshot([make_nm("default", 1.0, 512.0)])
    aggregator.clear()
    assert aggregator.aggregate() == []
    assert aggregator.namespace_count == 0
