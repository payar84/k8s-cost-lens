"""Tests for CostSpikeDetector."""
import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_spike import CostSpikeDetector, SpikeResult


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=hourly * 0.6,
        memory_cost=hourly * 0.4,
    )


@pytest.fixture
def detector() -> CostSpikeDetector:
    return CostSpikeDetector(threshold_pct=50.0)


def test_no_previous_new_namespace_is_spike(detector):
    current = [make_cost("ns-a", 1.0)]
    results = detector.detect([], current)
    assert len(results) == 1
    assert results[0].is_spike is True
    assert results[0].hourly_pct_change is None


def test_no_change_is_not_spike(detector):
    prev = [make_cost("ns-a", 1.0)]
    curr = [make_cost("ns-a", 1.0)]
    results = detector.detect(prev, curr)
    assert results[0].is_spike is False
    assert results[0].hourly_pct_change == pytest.approx(0.0)


def test_below_threshold_is_not_spike(detector):
    prev = [make_cost("ns-a", 1.0)]
    curr = [make_cost("ns-a", 1.4)]  # +40%, threshold is 50%
    results = detector.detect(prev, curr)
    assert results[0].is_spike is False


def test_above_threshold_is_spike(detector):
    prev = [make_cost("ns-a", 1.0)]
    curr = [make_cost("ns-a", 2.0)]  # +100%
    results = detector.detect(prev, curr)
    assert results[0].is_spike is True
    assert results[0].hourly_pct_change == pytest.approx(100.0)


def test_deltas_are_correct(detector):
    prev = [make_cost("ns-a", 2.0)]
    curr = [make_cost("ns-a", 3.0)]
    r = detector.detect(prev, curr)[0]
    assert r.hourly_delta == pytest.approx(1.0)
    assert r.monthly_delta == pytest.approx(720.0)


def test_spikes_only_filters_correctly(detector):
    prev = [make_cost("ns-a", 1.0), make_cost("ns-b", 1.0)]
    curr = [make_cost("ns-a", 2.0), make_cost("ns-b", 1.1)]
    results = detector.detect(prev, curr)
    spikes = detector.spikes_only(results)
    assert len(spikes) == 1
    assert spikes[0].namespace == "ns-a"


def test_empty_current_returns_empty(detector):
    prev = [make_cost("ns-a", 1.0)]
    results = detector.detect(prev, [])
    assert results == []


def test_negative_threshold_raises():
    with pytest.raises(ValueError):
        CostSpikeDetector(threshold_pct=-1.0)


def test_zero_current_cost_not_spike(detector):
    prev = [make_cost("ns-a", 1.0)]
    curr = [make_cost("ns-a", 0.0)]  # cost dropped, not a spike
    results = detector.detect(prev, curr)
    assert results[0].is_spike is False
    assert results[0].hourly_pct_change == pytest.approx(-100.0)
