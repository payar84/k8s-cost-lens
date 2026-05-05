"""Tests for CostBaselineManager."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_baseline import (
    CostBaselineManager,
    BaselineDiff,
)


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_hourly=hourly / 2,
        memory_hourly=hourly / 2,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture
def manager() -> CostBaselineManager:
    return CostBaselineManager()


@pytest.fixture
def sample_costs():
    return [make_cost("ns-a", 1.0), make_cost("ns-b", 2.0)]


def test_record_creates_baseline(manager, sample_costs):
    bl = manager.record("v1", sample_costs)
    assert bl.name == "v1"
    assert len(bl.entries) == 2


def test_get_returns_none_for_missing(manager):
    assert manager.get("missing") is None


def test_get_returns_recorded_baseline(manager, sample_costs):
    manager.record("v1", sample_costs)
    bl = manager.get("v1")
    assert bl is not None
    assert bl.name == "v1"


def test_list_names_empty(manager):
    assert manager.list_names() == []


def test_list_names_after_record(manager, sample_costs):
    manager.record("v1", sample_costs)
    manager.record("v2", sample_costs)
    assert set(manager.list_names()) == {"v1", "v2"}


def test_compare_raises_for_missing_baseline(manager, sample_costs):
    with pytest.raises(KeyError, match="no-such"):
        manager.compare("no-such", sample_costs)


def test_compare_returns_diff_per_namespace(manager, sample_costs):
    manager.record("v1", sample_costs)
    current = [make_cost("ns-a", 1.5), make_cost("ns-b", 2.0)]
    diffs = manager.compare("v1", current)
    assert len(diffs) == 2
    ns_a = next(d for d in diffs if d.namespace == "ns-a")
    assert abs(ns_a.hourly_delta - 0.5) < 1e-9


def test_compare_new_namespace_has_zero_baseline(manager, sample_costs):
    manager.record("v1", sample_costs)
    current = [make_cost("ns-new", 3.0)]
    diffs = manager.compare("v1", current)
    assert diffs[0].baseline_hourly == 0.0
    assert diffs[0].hourly_delta == 3.0


def test_hourly_pct_change_none_when_baseline_zero(manager):
    manager.record("v1", [])
    diffs = manager.compare("v1", [make_cost("ns-x", 1.0)])
    assert diffs[0].hourly_pct_change is None


def test_hourly_pct_change_calculated_correctly(manager, sample_costs):
    manager.record("v1", sample_costs)
    current = [make_cost("ns-a", 2.0), make_cost("ns-b", 2.0)]
    diffs = manager.compare("v1", current)
    ns_a = next(d for d in diffs if d.namespace == "ns-a")
    assert abs(ns_a.hourly_pct_change - 100.0) < 1e-6


def test_delete_existing_baseline(manager, sample_costs):
    manager.record("v1", sample_costs)
    assert manager.delete("v1") is True
    assert manager.get("v1") is None


def test_delete_missing_returns_false(manager):
    assert manager.delete("ghost") is False
