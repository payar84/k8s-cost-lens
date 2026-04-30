"""Tests for NamespaceGrouper."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.namespace_grouper import GroupedCost, NamespaceGrouper


def make_cost(namespace: str, hourly: float = 0.10, monthly: float = 72.0) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_cores=1.0,
        memory_gib=2.0,
        hourly_usd=hourly,
        monthly_usd=monthly,
    )


@pytest.fixture()
def grouper() -> NamespaceGrouper:
    return NamespaceGrouper(
        mapping={
            "platform": ["kube-system", "monitoring"],
            "product": ["frontend", "backend"],
        },
        default_group="other",
    )


def test_empty_costs_returns_empty(grouper: NamespaceGrouper) -> None:
    assert grouper.group([]) == []


def test_known_namespaces_are_grouped(grouper: NamespaceGrouper) -> None:
    costs = [
        make_cost("kube-system"),
        make_cost("monitoring"),
        make_cost("frontend"),
    ]
    result = grouper.group(costs)
    group_names = {g.group_name for g in result}
    assert "platform" in group_names
    assert "product" in group_names


def test_unknown_namespace_goes_to_default(grouper: NamespaceGrouper) -> None:
    costs = [make_cost("my-app")]
    result = grouper.group(costs)
    assert len(result) == 1
    assert result[0].group_name == "other"
    assert "my-app" in result[0].namespaces


def test_totals_are_summed_correctly(grouper: NamespaceGrouper) -> None:
    costs = [
        make_cost("kube-system", hourly=0.05, monthly=36.0),
        make_cost("monitoring", hourly=0.10, monthly=72.0),
    ]
    result = grouper.group(costs)
    assert len(result) == 1
    gc = result[0]
    assert gc.group_name == "platform"
    assert gc.total_hourly_usd == pytest.approx(0.15)
    assert gc.total_monthly_usd == pytest.approx(108.0)


def test_namespaces_list_is_sorted(grouper: NamespaceGrouper) -> None:
    costs = [
        make_cost("monitoring"),
        make_cost("kube-system"),
    ]
    result = grouper.group(costs)
    platform_group = next(g for g in result if g.group_name == "platform")
    assert platform_group.namespaces == ["kube-system", "monitoring"]


def test_no_mapping_all_go_to_default() -> None:
    grouper = NamespaceGrouper()
    costs = [make_cost("ns-a"), make_cost("ns-b")]
    result = grouper.group(costs)
    assert len(result) == 1
    assert result[0].group_name == "other"
    assert set(result[0].namespaces) == {"ns-a", "ns-b"}


def test_custom_default_group_name() -> None:
    grouper = NamespaceGrouper(default_group="ungrouped")
    costs = [make_cost("random-ns")]
    result = grouper.group(costs)
    assert result[0].group_name == "ungrouped"


def test_cpu_and_memory_totals(grouper: NamespaceGrouper) -> None:
    costs = [
        NamespaceCost(namespace="frontend", cpu_cores=2.0, memory_gib=4.0, hourly_usd=0.1, monthly_usd=72.0),
        NamespaceCost(namespace="backend", cpu_cores=3.0, memory_gib=6.0, hourly_usd=0.15, monthly_usd=108.0),
    ]
    result = grouper.group(costs)
    product_group = next(g for g in result if g.group_name == "product")
    assert product_group.total_cpu_cores == pytest.approx(5.0)
    assert product_group.total_memory_gib == pytest.approx(10.0)
