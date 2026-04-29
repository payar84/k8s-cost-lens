"""Tests for CostForecaster."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.aggregator import AggregatedMetrics
from k8s_cost_lens.metrics.cost_estimator import CostEstimator
from k8s_cost_lens.metrics.forecast import CostForecaster, ForecastResult


CPU_PRICE = 0.048
MEM_PRICE = 0.006


def make_agg(namespace: str, cpu: float, memory_gb: float) -> AggregatedMetrics:
    return AggregatedMetrics(namespace=namespace, avg_cpu_cores=cpu, avg_memory_gb=memory_gb)


@pytest.fixture()
def estimator() -> CostEstimator:
    return CostEstimator(cpu_hourly_price=CPU_PRICE, memory_gb_hourly_price=MEM_PRICE)


@pytest.fixture()
def forecaster(estimator: CostEstimator) -> CostForecaster:
    return CostForecaster(estimator=estimator, forecast_intervals=1)


def test_no_snapshots_returns_empty(forecaster: CostForecaster) -> None:
    assert forecaster.forecast() == []


def test_invalid_forecast_intervals(estimator: CostEstimator) -> None:
    with pytest.raises(ValueError):
        CostForecaster(estimator=estimator, forecast_intervals=0)


def test_single_snapshot_slope_is_zero(forecaster: CostForecaster) -> None:
    forecaster.add_snapshot([make_agg("ns-a", cpu=1.0, memory_gb=2.0)])
    results = forecaster.forecast()
    assert len(results) == 1
    assert results[0].slope == pytest.approx(0.0)
    assert results[0].current_hourly == pytest.approx(results[0].forecasted_hourly)


def test_stable_series_gives_zero_slope(forecaster: CostForecaster) -> None:
    for _ in range(4):
        forecaster.add_snapshot([make_agg("ns-a", cpu=2.0, memory_gb=4.0)])
    results = forecaster.forecast()
    assert results[0].slope == pytest.approx(0.0)
    assert results[0].trend_direction == "stable"


def test_increasing_series_positive_slope(forecaster: CostForecaster) -> None:
    for i in range(1, 5):
        forecaster.add_snapshot([make_agg("ns-a", cpu=float(i), memory_gb=0.0)])
    results = forecaster.forecast()
    assert results[0].slope > 0
    assert results[0].trend_direction == "increasing"
    assert results[0].forecasted_hourly > results[0].current_hourly


def test_decreasing_series_negative_slope(forecaster: CostForecaster) -> None:
    for i in range(4, 0, -1):
        forecaster.add_snapshot([make_agg("ns-a", cpu=float(i), memory_gb=0.0)])
    results = forecaster.forecast()
    assert results[0].slope < 0
    assert results[0].trend_direction == "decreasing"


def test_forecasted_hourly_never_negative(forecaster: CostForecaster) -> None:
    # Sharply declining series that would go negative without clamping
    for i in range(5, 0, -1):
        forecaster.add_snapshot([make_agg("ns-a", cpu=float(i) * 0.01, memory_gb=0.0)])
    results = forecaster.forecast()
    assert results[0].forecasted_hourly >= 0.0


def test_monthly_is_hourly_times_720(forecaster: CostForecaster) -> None:
    forecaster.add_snapshot([make_agg("ns-a", cpu=2.0, memory_gb=4.0)])
    r = forecaster.forecast()[0]
    assert r.forecasted_monthly == pytest.approx(r.forecasted_hourly * 720)


def test_multiple_namespaces_all_returned(forecaster: CostForecaster) -> None:
    forecaster.add_snapshot(
        [make_agg("ns-a", cpu=1.0, memory_gb=1.0), make_agg("ns-b", cpu=2.0, memory_gb=2.0)]
    )
    results = forecaster.forecast()
    namespaces = {r.namespace for r in results}
    assert namespaces == {"ns-a", "ns-b"}
