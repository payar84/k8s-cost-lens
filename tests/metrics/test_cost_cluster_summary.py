"""Tests for ClusterCostSummarizer."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_cluster_summary import (
    ClusterCostSummarizer,
    ClusterCostSummary,
)


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture()
def summarizer() -> ClusterCostSummarizer:
    return ClusterCostSummarizer()


# ---------------------------------------------------------------------------
# empty input
# ---------------------------------------------------------------------------

def test_empty_costs_returns_zero_summary(summarizer: ClusterCostSummarizer) -> None:
    result = summarizer.summarize([])
    assert isinstance(result, ClusterCostSummary)
    assert result.total_hourly == 0.0
    assert result.total_monthly == 0.0
    assert result.namespace_count == 0
    assert result.max_hourly_namespace is None
    assert result.min_hourly_namespace is None


# ---------------------------------------------------------------------------
# single namespace
# ---------------------------------------------------------------------------

def test_single_namespace_totals(summarizer: ClusterCostSummarizer) -> None:
    costs = [make_cost("default", 0.05)]
    result = summarizer.summarize(costs)
    assert result.namespace_count == 1
    assert result.total_hourly == pytest.approx(0.05)
    assert result.total_monthly == pytest.approx(0.05 * 720)


def test_single_namespace_avg_equals_total(summarizer: ClusterCostSummarizer) -> None:
    costs = [make_cost("default", 0.08)]
    result = summarizer.summarize(costs)
    assert result.avg_hourly_per_namespace == pytest.approx(result.total_hourly)
    assert result.avg_monthly_per_namespace == pytest.approx(result.total_monthly)


def test_single_namespace_max_and_min_are_same(summarizer: ClusterCostSummarizer) -> None:
    costs = [make_cost("default", 0.10)]
    result = summarizer.summarize(costs)
    assert result.max_hourly_namespace == "default"
    assert result.min_hourly_namespace == "default"


# ---------------------------------------------------------------------------
# multiple namespaces
# ---------------------------------------------------------------------------

def test_multiple_namespaces_total(summarizer: ClusterCostSummarizer) -> None:
    costs = [
        make_cost("ns-a", 0.10),
        make_cost("ns-b", 0.20),
        make_cost("ns-c", 0.30),
    ]
    result = summarizer.summarize(costs)
    assert result.total_hourly == pytest.approx(0.60)
    assert result.total_monthly == pytest.approx(0.60 * 720)


def test_multiple_namespaces_avg(summarizer: ClusterCostSummarizer) -> None:
    costs = [
        make_cost("ns-a", 0.10),
        make_cost("ns-b", 0.20),
        make_cost("ns-c", 0.30),
    ]
    result = summarizer.summarize(costs)
    assert result.avg_hourly_per_namespace == pytest.approx(0.20)


def test_max_namespace_identified(summarizer: ClusterCostSummarizer) -> None:
    costs = [
        make_cost("cheap", 0.01),
        make_cost("expensive", 0.99),
        make_cost("medium", 0.50),
    ]
    result = summarizer.summarize(costs)
    assert result.max_hourly_namespace == "expensive"
    assert result.max_hourly_cost == pytest.approx(0.99)


def test_min_namespace_identified(summarizer: ClusterCostSummarizer) -> None:
    costs = [
        make_cost("cheap", 0.01),
        make_cost("expensive", 0.99),
        make_cost("medium", 0.50),
    ]
    result = summarizer.summarize(costs)
    assert result.min_hourly_namespace == "cheap"
    assert result.min_hourly_cost == pytest.approx(0.01)


def test_namespace_count(summarizer: ClusterCostSummarizer) -> None:
    costs = [make_cost(f"ns-{i}", float(i)) for i in range(1, 6)]
    result = summarizer.summarize(costs)
    assert result.namespace_count == 5
