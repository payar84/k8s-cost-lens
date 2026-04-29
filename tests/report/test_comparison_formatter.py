"""Tests for CostComparisonFormatter."""

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.report.comparison_formatter import CostComparisonFormatter


def make_cost(namespace: str, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        cpu_cost=hourly * 0.6,
        memory_cost=hourly * 0.4,
    )


@pytest.fixture
def before():
    return [
        make_cost("default", 1.0),
        make_cost("kube-system", 0.5),
    ]


@pytest.fixture
def after():
    return [
        make_cost("default", 1.5),
        make_cost("kube-system", 0.5),
        make_cost("monitoring", 0.2),
    ]


@pytest.fixture
def formatter(before, after):
    return CostComparisonFormatter(before, after)


def test_as_table_returns_string(formatter):
    result = formatter.as_table()
    assert isinstance(result, str)


def test_as_table_contains_headers(formatter):
    result = formatter.as_table()
    assert "Namespace" in result
    assert "Hourly Before" in result
    assert "Hourly After" in result
    assert "Monthly Diff" in result


def test_as_table_contains_all_namespaces(formatter):
    result = formatter.as_table()
    assert "default" in result
    assert "kube-system" in result
    assert "monitoring" in result


def test_new_namespace_has_zero_before(after):
    fmt = CostComparisonFormatter([], after)
    rows = fmt._to_rows()
    monitoring = next(r for r in rows if r.namespace == "monitoring")
    assert monitoring.hourly_before == 0.0
    assert monitoring.monthly_before == 0.0


def test_removed_namespace_has_zero_after(before):
    fmt = CostComparisonFormatter(before, [])
    rows = fmt._to_rows()
    default_row = next(r for r in rows if r.namespace == "default")
    assert default_row.hourly_after == 0.0


def test_diff_is_after_minus_before(before, after):
    fmt = CostComparisonFormatter(before, after)
    rows = fmt._to_rows()
    default_row = next(r for r in rows if r.namespace == "default")
    assert abs(default_row.hourly_diff - 0.5) < 1e-9


def test_no_change_gives_zero_diff(before, after):
    fmt = CostComparisonFormatter(before, after)
    rows = fmt._to_rows()
    ks_row = next(r for r in rows if r.namespace == "kube-system")
    assert ks_row.hourly_diff == pytest.approx(0.0)
    assert ks_row.hourly_diff_pct == pytest.approx(0.0)


def test_pct_change_none_when_before_zero(after):
    fmt = CostComparisonFormatter([], after)
    rows = fmt._to_rows()
    monitoring = next(r for r in rows if r.namespace == "monitoring")
    assert monitoring.hourly_diff_pct is None
    assert monitoring.monthly_diff_pct is None


def test_as_csv_first_line_is_header(formatter):
    csv_output = formatter.as_csv()
    first_line = csv_output.splitlines()[0]
    assert "Namespace" in first_line
    assert "Hourly Before ($)" in first_line


def test_as_csv_contains_all_namespaces(formatter):
    csv_output = formatter.as_csv()
    assert "default" in csv_output
    assert "kube-system" in csv_output
    assert "monitoring" in csv_output


def test_empty_before_and_after():
    fmt = CostComparisonFormatter([], [])
    result = fmt.as_table()
    assert isinstance(result, str)
    lines = result.strip().splitlines()
    assert len(lines) == 1  # header only
