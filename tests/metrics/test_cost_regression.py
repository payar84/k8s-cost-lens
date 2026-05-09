"""Tests for CostRegressionAnalyzer and _linreg."""
import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.cost_regression import (
    CostRegressionAnalyzer,
    RegressionResult,
    _linreg,
)


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=hourly * 0.6,
        memory_cost=hourly * 0.4,
    )


@pytest.fixture
def analyzer() -> CostRegressionAnalyzer:
    return CostRegressionAnalyzer()


def test_no_snapshots_returns_empty(analyzer):
    assert analyzer.analyze() == []


def test_single_snapshot_returns_flat_slope(analyzer):
    analyzer.add_snapshot([make_cost("ns-a", 1.0)])
    results = analyzer.analyze()
    assert len(results) == 1
    assert results[0].slope_hourly == 0.0
    assert results[0].namespace == "ns-a"


def test_rising_trend_has_positive_slope(analyzer):
    for i in range(5):
        analyzer.add_snapshot([make_cost("ns-a", float(i + 1))])
    results = analyzer.analyze()
    assert results[0].slope_hourly > 0


def test_falling_trend_has_negative_slope(analyzer):
    for i in range(5):
        analyzer.add_snapshot([make_cost("ns-a", float(5 - i))])
    results = analyzer.analyze()
    assert results[0].slope_hourly < 0


def test_constant_series_gives_r_squared_one_or_zero(analyzer):
    for _ in range(4):
        analyzer.add_snapshot([make_cost("ns-x", 2.5)])
    results = analyzer.analyze()
    # ss_yy == 0, so r_squared is forced to 1.0
    assert results[0].r_squared == 1.0


def test_predicted_monthly_is_hourly_times_720(analyzer):
    for i in range(3):
        analyzer.add_snapshot([make_cost("ns-a", float(i + 1))])
    result = analyzer.analyze()[0]
    assert abs(result.predicted_next_monthly - result.predicted_next_hourly * 720) < 1e-9


def test_multiple_namespaces_all_returned(analyzer):
    analyzer.add_snapshot([make_cost("ns-a", 1.0), make_cost("ns-b", 2.0)])
    analyzer.add_snapshot([make_cost("ns-a", 1.5), make_cost("ns-b", 1.5)])
    results = analyzer.analyze()
    namespaces = {r.namespace for r in results}
    assert namespaces == {"ns-a", "ns-b"}


def test_results_sorted_by_predicted_monthly_desc(analyzer):
    for i in range(3):
        analyzer.add_snapshot([
            make_cost("cheap", 0.1),
            make_cost("expensive", 5.0),
        ])
    results = analyzer.analyze()
    assert results[0].namespace == "expensive"


def test_missing_namespace_in_snapshot_treated_as_zero(analyzer):
    analyzer.add_snapshot([make_cost("ns-a", 1.0), make_cost("ns-b", 2.0)])
    analyzer.add_snapshot([make_cost("ns-a", 1.0)])  # ns-b absent
    results = analyzer.analyze()
    ns_b = next(r for r in results if r.namespace == "ns-b")
    assert ns_b.slope_hourly < 0  # went from 2.0 to 0.0


def test_linreg_perfect_line():
    xs = [0.0, 1.0, 2.0, 3.0]
    ys = [1.0, 2.0, 3.0, 4.0]
    slope, intercept, r2 = _linreg(xs, ys)
    assert abs(slope - 1.0) < 1e-9
    assert abs(intercept - 1.0) < 1e-9
    assert abs(r2 - 1.0) < 1e-9


def test_add_empty_snapshot_is_ignored(analyzer):
    analyzer.add_snapshot([])
    assert analyzer.analyze() == []
