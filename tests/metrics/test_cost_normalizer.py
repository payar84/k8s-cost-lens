"""Tests for CostNormalizer."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_normalizer import CostNormalizer, NormalizedCost


def make_cost(ns: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=ns,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture()
def sample_costs():
    return [
        make_cost("ns-a", 1.0),
        make_cost("ns-b", 3.0),
        make_cost("ns-c", 6.0),
    ]


# ---------------------------------------------------------------------------
# empty input
# ---------------------------------------------------------------------------

def test_empty_returns_empty():
    normalizer = CostNormalizer()
    assert normalizer.normalize([]) == []


# ---------------------------------------------------------------------------
# total reference (default)
# ---------------------------------------------------------------------------

def test_total_reference_shares_sum_to_one(sample_costs):
    normalizer = CostNormalizer(reference="total")
    results = normalizer.normalize(sample_costs)
    total_share = sum(r.hourly_share for r in results)
    assert abs(total_share - 1.0) < 1e-9


def test_total_reference_correct_share(sample_costs):
    normalizer = CostNormalizer(reference="total")
    results = normalizer.normalize(sample_costs)
    by_ns = {r.namespace: r for r in results}
    # ns-c is 6/10 = 0.6
    assert abs(by_ns["ns-c"].hourly_share - 0.6) < 1e-9


def test_total_reference_value_stored(sample_costs):
    normalizer = CostNormalizer(reference="total")
    results = normalizer.normalize(sample_costs)
    for r in results:
        assert r.reference_hourly == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# peak reference
# ---------------------------------------------------------------------------

def test_peak_reference_max_share_is_one(sample_costs):
    normalizer = CostNormalizer(reference="peak")
    results = normalizer.normalize(sample_costs)
    assert max(r.hourly_share for r in results) == pytest.approx(1.0)


def test_peak_reference_smaller_namespace(sample_costs):
    normalizer = CostNormalizer(reference="peak")
    results = normalizer.normalize(sample_costs)
    by_ns = {r.namespace: r for r in results}
    # ns-a is 1/6
    assert by_ns["ns-a"].hourly_share == pytest.approx(1.0 / 6.0)


# ---------------------------------------------------------------------------
# named namespace reference
# ---------------------------------------------------------------------------

def test_named_reference_that_namespace_has_share_one(sample_costs):
    normalizer = CostNormalizer(reference="ns-b")
    results = normalizer.normalize(sample_costs)
    by_ns = {r.namespace: r for r in results}
    assert by_ns["ns-b"].hourly_share == pytest.approx(1.0)


def test_named_reference_other_namespace_share(sample_costs):
    normalizer = CostNormalizer(reference="ns-b")
    results = normalizer.normalize(sample_costs)
    by_ns = {r.namespace: r for r in results}
    # ns-c is 6/3 = 2.0
    assert by_ns["ns-c"].hourly_share == pytest.approx(2.0)


def test_named_reference_missing_raises(sample_costs):
    normalizer = CostNormalizer(reference="does-not-exist")
    with pytest.raises(ValueError, match="does-not-exist"):
        normalizer.normalize(sample_costs)


# ---------------------------------------------------------------------------
# str representation
# ---------------------------------------------------------------------------

def test_str_contains_namespace():
    result = NormalizedCost(
        namespace="my-ns",
        hourly_cost=2.0,
        monthly_cost=1440.0,
        hourly_share=0.5,
        monthly_share=0.5,
        reference_hourly=4.0,
        reference_monthly=2880.0,
    )
    assert "my-ns" in str(result)
    assert "50.0%" in str(result)
