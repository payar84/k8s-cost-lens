"""Tests for CostSorter."""
import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_sorter import CostSorter, SortKey, SortOrder


def make_cost(namespace: str, hourly: float, cpu: float = 0.0, mem: float = 0.0) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=cpu,
        memory_cost=mem,
    )


@pytest.fixture
def sample_costs():
    return [
        make_cost("alpha", hourly=0.10, cpu=0.06, mem=0.04),
        make_cost("beta", hourly=0.50, cpu=0.30, mem=0.20),
        make_cost("gamma", hourly=0.25, cpu=0.15, mem=0.10),
    ]


def test_sort_by_monthly_desc(sample_costs):
    sorter = CostSorter(key=SortKey.MONTHLY, order=SortOrder.DESC)
    ranked = sorter.sort(sample_costs)
    assert ranked[0].cost.namespace == "beta"
    assert ranked[1].cost.namespace == "gamma"
    assert ranked[2].cost.namespace == "alpha"


def test_sort_by_hourly_asc(sample_costs):
    sorter = CostSorter(key=SortKey.HOURLY, order=SortOrder.ASC)
    ranked = sorter.sort(sample_costs)
    assert ranked[0].cost.namespace == "alpha"
    assert ranked[-1].cost.namespace == "beta"


def test_ranks_are_sequential(sample_costs):
    sorter = CostSorter()
    ranked = sorter.sort(sample_costs)
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_top_n_limits_results(sample_costs):
    sorter = CostSorter(key=SortKey.MONTHLY, order=SortOrder.DESC, top_n=2)
    ranked = sorter.sort(sample_costs)
    assert len(ranked) == 2
    assert ranked[0].cost.namespace == "beta"


def test_sort_by_namespace_asc(sample_costs):
    sorter = CostSorter(key=SortKey.NAMESPACE, order=SortOrder.ASC)
    ranked = sorter.sort(sample_costs)
    names = [r.cost.namespace for r in ranked]
    assert names == sorted(names)


def test_sort_by_cpu_desc(sample_costs):
    sorter = CostSorter(key=SortKey.CPU, order=SortOrder.DESC)
    ranked = sorter.sort(sample_costs)
    assert ranked[0].cost.namespace == "beta"


def test_sort_by_memory_desc(sample_costs):
    sorter = CostSorter(key=SortKey.MEMORY, order=SortOrder.DESC)
    ranked = sorter.sort(sample_costs)
    assert ranked[0].cost.namespace == "beta"


def test_empty_list_returns_empty():
    sorter = CostSorter()
    assert sorter.sort([]) == []


def test_str_representation(sample_costs):
    sorter = CostSorter(top_n=1)
    ranked = sorter.sort(sample_costs)
    result = str(ranked[0])
    assert "#1" in result
    assert "beta" in result
