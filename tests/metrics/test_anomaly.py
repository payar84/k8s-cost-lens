"""Tests for CostAnomalyDetector."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.anomaly import CostAnomalyDetector, AnomalyResult
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(namespace=namespace, hourly_cost=hourly, monthly_cost=hourly * 720)


@pytest.fixture
def detector() -> CostAnomalyDetector:
    return CostAnomalyDetector(threshold=2.0)


def test_detect_without_fit_returns_no_anomalies(detector):
    current = [make_cost("ns-a", 1.0), make_cost("ns-b", 100.0)]
    results = detector.detect(current)
    assert len(results) == 2
    assert all(not r.is_anomaly for r in results)


def test_detect_with_single_baseline_no_anomaly(detector):
    detector.fit([make_cost("ns-x", 5.0)])
    current = [make_cost("ns-a", 999.0)]
    results = detector.detect(current)
    assert results[0].is_anomaly is False
    assert results[0].z_score is None


def test_no_anomaly_when_all_costs_equal(detector):
    baseline = [make_cost(f"ns-{i}", 1.0) for i in range(5)]
    detector.fit(baseline)
    current = [make_cost("ns-new", 1.0)]
    results = detector.detect(current)
    assert results[0].is_anomaly is False
    assert results[0].z_score is None  # stddev == 0


def test_anomaly_detected_above_threshold(detector):
    # baseline: costs 1..10, mean=5.5, stdev~3.03
    baseline = [make_cost(f"ns-{i}", float(i + 1)) for i in range(10)]
    detector.fit(baseline)
    # z = (50 - 5.5) / 3.03 >> 2.0 -> anomaly
    current = [make_cost("ns-spike", 50.0)]
    results = detector.detect(current)
    assert results[0].is_anomaly is True
    assert results[0].z_score is not None
    assert results[0].z_score > 2.0


def test_normal_cost_not_flagged(detector):
    baseline = [make_cost(f"ns-{i}", float(i + 1)) for i in range(10)]
    detector.fit(baseline)
    current = [make_cost("ns-normal", 5.5)]
    results = detector.detect(current)
    assert results[0].is_anomaly is False


def test_anomalies_only_filters_correctly(detector):
    baseline = [make_cost(f"ns-{i}", float(i + 1)) for i in range(10)]
    detector.fit(baseline)
    current = [
        make_cost("ns-normal", 5.5),
        make_cost("ns-spike", 50.0),
    ]
    anomalies = detector.anomalies_only(current)
    assert len(anomalies) == 1
    assert anomalies[0].namespace == "ns-spike"


def test_result_str_contains_namespace(detector):
    baseline = [make_cost(f"ns-{i}", float(i + 1)) for i in range(10)]
    detector.fit(baseline)
    current = [make_cost("ns-spike", 50.0)]
    result = detector.detect(current)[0]
    assert "ns-spike" in str(result)
    assert "ANOMALY" in str(result)


def test_custom_threshold_respected():
    det = CostAnomalyDetector(threshold=1.0)
    baseline = [make_cost(f"ns-{i}", float(i + 1)) for i in range(10)]
    det.fit(baseline)
    # z slightly above 1.0 should trigger with threshold=1.0
    current = [make_cost("ns-edge", 9.0)]
    results = det.detect(current)
    assert results[0].is_anomaly is True
