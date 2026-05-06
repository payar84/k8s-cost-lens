"""Tests for PrometheusMetricsFormatter."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_exporter import CostMetricsExporter
from k8s_cost_lens.report.exporter_formatter import PrometheusMetricsFormatter


def make_cost(namespace: str, hourly: float = 1.0) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture
def formatter() -> PrometheusMetricsFormatter:
    return PrometheusMetricsFormatter()


@pytest.fixture
def sample_costs() -> list:
    return [make_cost("default", 1.0), make_cost("kube-system", 0.5)]


def test_as_table_returns_string(formatter, sample_costs):
    result = formatter.as_table(sample_costs)
    assert isinstance(result, str)


def test_as_table_contains_headers(formatter, sample_costs):
    result = formatter.as_table(sample_costs)
    assert "Namespace" in result
    assert "Metric" in result
    assert "Value" in result


def test_as_table_contains_namespace_names(formatter, sample_costs):
    result = formatter.as_table(sample_costs)
    assert "default" in result
    assert "kube-system" in result


def test_as_table_contains_metric_names(formatter, sample_costs):
    result = formatter.as_table(sample_costs)
    assert "hourly_cost_usd" in result
    assert "monthly_cost_usd" in result


def test_as_table_empty_costs_returns_no_metrics_message(formatter):
    result = formatter.as_table([])
    assert "No metrics" in result


def test_as_text_returns_prometheus_format(formatter, sample_costs):
    result = formatter.as_text(sample_costs)
    assert "# HELP" in result
    assert "# TYPE" in result


def test_as_text_contains_namespace_label(formatter, sample_costs):
    result = formatter.as_text(sample_costs)
    assert 'namespace="default"' in result
    assert 'namespace="kube-system"' in result


def test_custom_exporter_prefix_is_used(sample_costs):
    exp = CostMetricsExporter(prefix="custom_prefix")
    fmt = PrometheusMetricsFormatter(exporter=exp)
    result = fmt.as_table(sample_costs)
    assert "custom_prefix" in result


def test_extra_labels_appear_in_text(sample_costs):
    exp = CostMetricsExporter(extra_labels={"cluster": "staging"})
    fmt = PrometheusMetricsFormatter(exporter=exp)
    result = fmt.as_text(sample_costs)
    assert 'cluster="staging"' in result
