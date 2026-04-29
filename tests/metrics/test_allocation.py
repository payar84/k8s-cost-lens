"""Tests for CostAllocator."""
import pytest

from k8s_cost_lens.metrics.allocation import (
    AllocationWeights,
    AllocationResult,
    CostAllocator,
)
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


def make_cost(ns: str, cpu: float, mem: int, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=ns,
        cpu_cores=cpu,
        memory_bytes=mem,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture
def allocator() -> CostAllocator:
    return CostAllocator()


def test_empty_costs_returns_empty(allocator: CostAllocator) -> None:
    assert allocator.allocate([]) == []


def test_single_namespace_gets_full_share(allocator: CostAllocator) -> None:
    costs = [make_cost("default", 1.0, 1_000_000, 0.10)]
    results = allocator.allocate(costs)
    assert len(results) == 1
    assert results[0].share_pct == pytest.approx(100.0)
    assert results[0].allocated_hourly == pytest.approx(0.10)
    assert results[0].allocated_monthly == pytest.approx(0.10 * 720)


def test_equal_resources_split_evenly(allocator: CostAllocator) -> None:
    costs = [
        make_cost("ns-a", 1.0, 1_000_000, 0.05),
        make_cost("ns-b", 1.0, 1_000_000, 0.05),
    ]
    results = allocator.allocate(costs)
    shares = {r.namespace: r.share_pct for r in results}
    assert shares["ns-a"] == pytest.approx(50.0)
    assert shares["ns-b"] == pytest.approx(50.0)


def test_shares_sum_to_100(allocator: CostAllocator) -> None:
    costs = [
        make_cost("ns-a", 2.0, 500_000, 0.04),
        make_cost("ns-b", 0.5, 2_000_000, 0.06),
        make_cost("ns-c", 1.0, 1_000_000, 0.02),
    ]
    results = allocator.allocate(costs)
    total_share = sum(r.share_pct for r in results)
    assert total_share == pytest.approx(100.0, abs=1e-6)


def test_custom_weights_affect_allocation() -> None:
    weights = AllocationWeights(cpu_weight=1.0, memory_weight=0.0)
    allocator = CostAllocator(weights=weights)
    costs = [
        make_cost("cpu-heavy", 3.0, 1_000_000, 0.06),
        make_cost("mem-heavy", 1.0, 9_000_000, 0.04),
    ]
    results = allocator.allocate(costs)
    by_ns = {r.namespace: r for r in results}
    # With cpu_weight=1.0 cpu-heavy has 3/4 = 75% share
    assert by_ns["cpu-heavy"].share_pct == pytest.approx(75.0)
    assert by_ns["mem-heavy"].share_pct == pytest.approx(25.0)


def test_invalid_weights_raise() -> None:
    with pytest.raises(ValueError, match="must equal 1.0"):
        AllocationWeights(cpu_weight=0.6, memory_weight=0.6)


def test_zero_cpu_falls_back_to_memory_share() -> None:
    weights = AllocationWeights(cpu_weight=0.5, memory_weight=0.5)
    allocator = CostAllocator(weights=weights)
    costs = [
        make_cost("ns-a", 0.0, 1_000_000, 0.05),
        make_cost("ns-b", 0.0, 3_000_000, 0.05),
    ]
    results = allocator.allocate(costs)
    by_ns = {r.namespace: r for r in results}
    assert by_ns["ns-a"].share_pct == pytest.approx(25.0)
    assert by_ns["ns-b"].share_pct == pytest.approx(75.0)
