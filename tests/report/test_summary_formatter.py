"""Tests for CostSummaryFormatter."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.report.summary_formatter import CostSummaryFormatter


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_hourly=hourly * 0.6,
        memory_hourly=hourly * 0.4,
    )


@pytest.fixture()
def sample_costs():
    return [
        make_cost("default", 0.10),
        make_cost("kube-system", 0.05),
        make_cost("monitoring", 0.20),
    ]


@pytest.fixture()
def formatter(sample_costs):
    return CostSummaryFormatter(sample_costs)


def test_as_table_returns_string(formatter):
    result = formatter.as_table()
    assert isinstance(result, str)


def test_as_table_contains_metric_labels(formatter):
    result = formatter.as_table()
    assert "Total hourly cost" in result
    assert "Total monthly cost" in result
    assert "Top namespace" in result


def test_as_table_identifies_top_namespace(formatter):
    result = formatter.as_table()
    assert "monitoring" in result


def test_as_dict_total_hourly(sample_costs):
    f = CostSummaryFormatter(sample_costs)
    d = f.as_dict()
    assert abs(d["total_hourly"] - 0.35) < 1e-6


def test_as_dict_total_monthly(sample_costs):
    f = CostSummaryFormatter(sample_costs)
    d = f.as_dict()
    assert abs(d["total_monthly"] - 0.35 * 720) < 1e-3


def test_as_dict_top_namespace(sample_costs):
    f = CostSummaryFormatter(sample_costs)
    assert f.as_dict()["top_namespace"] == "monitoring"


def test_as_dict_avg_hourly(sample_costs):
    f = CostSummaryFormatter(sample_costs)
    d = f.as_dict()
    assert abs(d["avg_hourly"] - (0.35 / 3)) < 1e-6


def test_empty_costs_returns_zero_stats():
    f = CostSummaryFormatter([])
    d = f.as_dict()
    assert d["total_namespaces"] == 0
    assert d["total_hourly"] == 0.0
    assert d["top_namespace"] == "—"


def test_empty_costs_table_does_not_raise():
    f = CostSummaryFormatter([])
    result = f.as_table()
    assert isinstance(result, str)


def test_single_namespace_is_top():
    f = CostSummaryFormatter([make_cost("only", 0.07)])
    assert f.as_dict()["top_namespace"] == "only"
