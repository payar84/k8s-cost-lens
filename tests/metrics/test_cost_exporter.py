"""Tests for CostMetricsExporter."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_exporter import CostMetricsExporter, ExportedMetric


def make_cost(namespace: str, hourly: float = 1.0) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture
def exporter() -> CostMetricsExporter:
    return CostMetricsExporter(prefix="k8s_cost_lens")


def test_export_returns_two_metrics_per_namespace(exporter):
    costs = [make_cost("default")]
    result = exporter.export(costs)
    assert len(result) == 2


def test_export_metric_names(exporter):
    costs = [make_cost("default", hourly=0.5)]
    result = exporter.export(costs)
    names = {m.name for m in result}
    assert "k8s_cost_lens_hourly_cost_usd" in names
    assert "k8s_cost_lens_monthly_cost_usd" in names


def test_export_hourly_value(exporter):
    costs = [make_cost("ns-a", hourly=2.5)]
    result = exporter.export(costs)
    hourly = next(m for m in result if "hourly" in m.name)
    assert hourly.value == pytest.approx(2.5)


def test_export_monthly_value(exporter):
    costs = [make_cost("ns-a", hourly=1.0)]
    result = exporter.export(costs)
    monthly = next(m for m in result if "monthly" in m.name)
    assert monthly.value == pytest.approx(720.0)


def test_namespace_label_is_set(exporter):
    costs = [make_cost("my-ns")]
    result = exporter.export(costs)
    for m in result:
        assert m.labels["namespace"] == "my-ns"


def test_extra_labels_are_included():
    exp = CostMetricsExporter(extra_labels={"cluster": "prod"})
    result = exp.export([make_cost("default")])
    for m in result:
        assert m.labels["cluster"] == "prod"


def test_exported_metric_str_format(exporter):
    m = ExportedMetric(name="test_metric", labels={"namespace": "foo"}, value=1.23)
    assert str(m) == 'test_metric{namespace="foo"} 1.23'


def test_as_text_contains_help_and_type(exporter):
    text = exporter.as_text([make_cost("default")])
    assert "# HELP k8s_cost_lens_hourly_cost_usd" in text
    assert "# TYPE k8s_cost_lens_hourly_cost_usd gauge" in text


def test_as_text_help_appears_once_per_metric_name(exporter):
    costs = [make_cost("ns-a"), make_cost("ns-b")]
    text = exporter.as_text(costs)
    assert text.count("# HELP k8s_cost_lens_hourly_cost_usd") == 1


def test_empty_costs_returns_empty_export(exporter):
    assert exporter.export([]) == []
    assert exporter.as_text([]) == ""
