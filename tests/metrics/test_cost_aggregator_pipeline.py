"""Tests for CostAggregatorPipeline."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_sorter import SortKey, SortOrder
from k8s_cost_lens.metrics.label_filter import LabelSelector
from k8s_cost_lens.metrics.cost_aggregator_pipeline import CostAggregatorPipeline


def make_cost(ns: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=ns,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=hourly * 0.6,
        memory_cost=hourly * 0.4,
    )


SAMPLE = [
    make_cost("alpha", 1.0),
    make_cost("beta", 3.0),
    make_cost("gamma", 2.0),
    make_cost("delta", 0.5),
]

NS_LABELS = {
    "alpha": {"team": "platform"},
    "beta": {"team": "data"},
    "gamma": {"team": "platform"},
    "delta": {"team": "data"},
}


@pytest.fixture()
def pipeline() -> CostAggregatorPipeline:
    return CostAggregatorPipeline()


# ---------------------------------------------------------------------------
# basic pipeline
# ---------------------------------------------------------------------------

def test_run_returns_pipeline_result(pipeline):
    result = pipeline.run(SAMPLE)
    assert len(result.filtered) == 4
    assert len(result.normalized) == 4


def test_default_sort_is_monthly_desc(pipeline):
    result = pipeline.run(SAMPLE)
    names = [c.namespace for c in result.sorted_costs]
    assert names == ["beta", "gamma", "alpha", "delta"]


def test_normalized_shares_sum_to_one(pipeline):
    result = pipeline.run(SAMPLE)
    total = sum(n.share for n in result.normalized)
    assert abs(total - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# top-N
# ---------------------------------------------------------------------------

def test_top_n_limits_output():
    pipe = CostAggregatorPipeline(top_n=2)
    result = pipe.run(SAMPLE)
    assert len(result.top_n) == 2
    assert len(result.normalized) == 2


def test_top_n_zero_keeps_all():
    pipe = CostAggregatorPipeline(top_n=0)
    result = pipe.run(SAMPLE)
    assert len(result.top_n) == 4


# ---------------------------------------------------------------------------
# label filter
# ---------------------------------------------------------------------------

def test_label_filter_reduces_set():
    selector = LabelSelector.from_string("team=platform")
    pipe = CostAggregatorPipeline(selector=selector)
    result = pipe.run(SAMPLE, namespace_labels=NS_LABELS)
    ns_names = {c.namespace for c in result.filtered}
    assert ns_names == {"alpha", "gamma"}


def test_no_labels_provided_skips_filter():
    selector = LabelSelector.from_string("team=platform")
    pipe = CostAggregatorPipeline(selector=selector)
    result = pipe.run(SAMPLE, namespace_labels=None)
    # filter stage is skipped – all four pass through
    assert len(result.filtered) == 4


# ---------------------------------------------------------------------------
# sort order
# ---------------------------------------------------------------------------

def test_asc_sort_order():
    pipe = CostAggregatorPipeline(sort_key=SortKey.HOURLY, sort_order=SortOrder.ASC)
    result = pipe.run(SAMPLE)
    hourly_values = [c.hourly_cost for c in result.sorted_costs]
    assert hourly_values == sorted(hourly_values)


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

def test_empty_costs_returns_empty_result(pipeline):
    result = pipeline.run([])
    assert result.filtered == []
    assert result.normalized == []
    assert len(result) == 0
