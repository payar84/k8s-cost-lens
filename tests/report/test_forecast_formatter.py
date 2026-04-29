"""Tests for ForecastReportFormatter."""
from __future__ import annotations

import csv
import io

import pytest

from k8s_cost_lens.metrics.forecast import ForecastResult
from k8s_cost_lens.report.forecast_formatter import ForecastReportFormatter


def make_result(
    namespace: str = "default",
    current_hourly: float = 0.10,
    forecasted_hourly: float = 0.12,
    slope: float = 0.02,
) -> ForecastResult:
    return ForecastResult(
        namespace=namespace,
        current_hourly=current_hourly,
        forecasted_hourly=forecasted_hourly,
        forecasted_monthly=forecasted_hourly * 720,
        slope=slope,
    )


@pytest.fixture()
def sample_results() -> list[ForecastResult]:
    return [
        make_result("ns-a", current_hourly=0.05, forecasted_hourly=0.07, slope=0.02),
        make_result("ns-b", current_hourly=0.10, forecasted_hourly=0.08, slope=-0.02),
        make_result("ns-c", current_hourly=0.03, forecasted_hourly=0.03, slope=0.0),
    ]


@pytest.fixture()
def formatter(sample_results: list[ForecastResult]) -> ForecastReportFormatter:
    return ForecastReportFormatter(sample_results)


def test_as_table_returns_string(formatter: ForecastReportFormatter) -> None:
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter: ForecastReportFormatter) -> None:
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Current $/hr" in table
    assert "Forecast $/hr" in table
    assert "Forecast $/mo" in table
    assert "Trend" in table


def test_as_table_contains_namespace_names(formatter: ForecastReportFormatter) -> None:
    table = formatter.as_table()
    assert "ns-a" in table
    assert "ns-b" in table
    assert "ns-c" in table


def test_as_table_shows_trend_directions(formatter: ForecastReportFormatter) -> None:
    table = formatter.as_table()
    assert "increasing" in table
    assert "decreasing" in table
    assert "stable" in table


def test_as_csv_returns_string(formatter: ForecastReportFormatter) -> None:
    assert isinstance(formatter.as_csv(), str)


def test_as_csv_is_parseable(formatter: ForecastReportFormatter) -> None:
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    # header + 3 data rows
    assert len(rows) == 4


def test_as_csv_header_row(formatter: ForecastReportFormatter) -> None:
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    header = next(reader)
    assert header[0] == "Namespace"
    assert "Forecast $/hr" in header


def test_as_csv_namespace_values(formatter: ForecastReportFormatter) -> None:
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    next(reader)  # skip header
    namespaces = [row[0] for row in reader]
    assert set(namespaces) == {"ns-a", "ns-b", "ns-c"}


def test_result_count(formatter: ForecastReportFormatter) -> None:
    assert formatter.result_count() == 3


def test_empty_formatter() -> None:
    f = ForecastReportFormatter([])
    assert f.result_count() == 0
    assert "Namespace" in f.as_table()
    rows = list(csv.reader(io.StringIO(f.as_csv())))
    assert len(rows) == 1  # header only
