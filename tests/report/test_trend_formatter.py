"""Tests for TrendReportFormatter."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.trend import NamespaceTrend
from k8s_cost_lens.report.trend_formatter import TrendReportFormatter


def make_trend(
    namespace: str,
    current_hourly: float,
    previous_hourly: float,
) -> NamespaceTrend:
    current = NamespaceCost(
        namespace=namespace,
        hourly_cost=current_hourly,
        monthly_cost=current_hourly * 720,
        cpu_hourly=current_hourly * 0.6,
        memory_hourly=current_hourly * 0.4,
    )
    delta = current_hourly - previous_hourly
    pct = (delta / previous_hourly * 100.0) if previous_hourly != 0 else None
    return NamespaceTrend(
        namespace=namespace,
        current_cost=current,
        previous_cost=previous_hourly,
        delta=delta,
        percent_change=pct,
    )


@pytest.fixture()
def sample_trends() -> list[NamespaceTrend]:
    return [
        make_trend("default", 0.05, 0.04),
        make_trend("kube-system", 0.02, 0.02),
        make_trend("monitoring", 0.01, 0.03),
    ]


@pytest.fixture()
def formatter(sample_trends: list[NamespaceTrend]) -> TrendReportFormatter:
    return TrendReportFormatter(sample_trends)


def test_as_table_contains_headers(formatter: TrendReportFormatter) -> None:
    table = formatter.as_table()
    for header in ["Namespace", "Curr $/hr", "Prev $/hr", "Delta $/hr", "Change %", "Direction"]:
        assert header in table


def test_as_table_contains_namespace_names(formatter: TrendReportFormatter) -> None:
    table = formatter.as_table()
    assert "default" in table
    assert "kube-system" in table
    assert "monitoring" in table


def test_as_table_up_direction(formatter: TrendReportFormatter) -> None:
    table = formatter.as_table()
    assert "↑ UP" in table


def test_as_table_flat_direction(formatter: TrendReportFormatter) -> None:
    table = formatter.as_table()
    assert "→ FLAT" in table


def test_as_table_down_direction(formatter: TrendReportFormatter) -> None:
    table = formatter.as_table()
    assert "↓ DOWN" in table


def test_as_csv_contains_headers(formatter: TrendReportFormatter) -> None:
    csv = formatter.as_csv()
    first_line = csv.splitlines()[0]
    assert "Namespace" in first_line
    assert "Change %" in first_line


def test_as_csv_row_count(formatter: TrendReportFormatter, sample_trends: list[NamespaceTrend]) -> None:
    csv = formatter.as_csv()
    lines = csv.splitlines()
    # header + one row per trend
    assert len(lines) == len(sample_trends) + 1


def test_as_csv_na_when_previous_zero() -> None:
    trend = make_trend("new-ns", 0.05, 0.0)
    fmt = TrendReportFormatter([trend])
    csv = fmt.as_csv()
    data_line = csv.splitlines()[1]
    parts = data_line.split(",")
    # percent_change column should be empty string
    assert parts[4] == ""


def test_empty_trends_table_has_only_header_and_separator() -> None:
    fmt = TrendReportFormatter([])
    table = fmt.as_table()
    lines = table.splitlines()
    assert len(lines) == 2  # header + separator
