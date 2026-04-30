"""Tests for CostRoller and RollingWindow."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.aggregator import AggregatedMetrics
from k8s_cost_lens.metrics.cost_estimator import CostEstimator
from k8s_cost_lens.metrics.cost_roller import CostRoller, RollingWindow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_agg(namespace: str, cpu_cores: float, memory_gib: float) -> AggregatedMetrics:
    return AggregatedMetrics(
        namespace=namespace,
        avg_cpu_cores=cpu_cores,
        avg_memory_gib=memory_gib,
        sample_count=1,
    )


@pytest.fixture()
def estimator() -> CostEstimator:
    return CostEstimator(cpu_price_per_core_hour=0.04, memory_price_per_gib_hour=0.01)


@pytest.fixture()
def roller(estimator: CostEstimator) -> CostRoller:
    return CostRoller(estimator=estimator, window_size=3)


# ---------------------------------------------------------------------------
# RollingWindow tests
# ---------------------------------------------------------------------------

def test_window_size_zero_raises():
    with pytest.raises(ValueError, match="window_size"):
        RollingWindow(window_size=0)


def test_window_evicts_oldest():
    w = RollingWindow(window_size=2)
    w.push(["a"])
    w.push(["b"])
    w.push(["c"])  # "a" should be evicted
    assert w.snapshots == [["b"], ["c"]]


def test_window_is_full():
    w = RollingWindow(window_size=2)
    assert not w.is_full
    w.push([])
    w.push([])
    assert w.is_full


def test_window_clear():
    w = RollingWindow(window_size=3)
    w.push([])
    w.clear()
    assert w.snapshots == []


# ---------------------------------------------------------------------------
# CostRoller tests
# ---------------------------------------------------------------------------

def test_empty_roller_returns_empty(roller: CostRoller):
    assert roller.rolling_costs() == []


def test_single_snapshot_rolling_cost(roller: CostRoller):
    snapshot = [make_agg("ns-a", cpu_cores=1.0, memory_gib=2.0)]
    roller.push(snapshot)
    results = roller.rolling_costs()
    assert len(results) == 1
    rc = results[0]
    assert rc.namespace == "ns-a"
    assert rc.sample_count == 1
    assert rc.avg_hourly == pytest.approx(0.04 * 1.0 + 0.01 * 2.0)


def test_multiple_snapshots_are_averaged(roller: CostRoller, estimator: CostEstimator):
    roller.push([make_agg("ns-a", 1.0, 0.0)])
    roller.push([make_agg("ns-a", 3.0, 0.0)])
    results = roller.rolling_costs()
    assert len(results) == 1
    rc = results[0]
    assert rc.sample_count == 2
    expected_avg_hourly = (0.04 * 1.0 + 0.04 * 3.0) / 2
    assert rc.avg_hourly == pytest.approx(expected_avg_hourly)


def test_window_size_property(roller: CostRoller):
    assert roller.window_size == 3


def test_results_sorted_by_namespace(roller: CostRoller):
    roller.push([
        make_agg("zzz", 1.0, 0.0),
        make_agg("aaa", 1.0, 0.0),
    ])
    results = roller.rolling_costs()
    names = [r.namespace for r in results]
    assert names == sorted(names)


def test_rolling_cost_str():
    from k8s_cost_lens.metrics.cost_roller import RollingCost
    rc = RollingCost(namespace="prod", avg_hourly=0.05, avg_monthly=36.0, sample_count=3)
    s = str(rc)
    assert "prod" in s
    assert "0.0500" in s
    assert "36.00" in s
    assert "n=3" in s
