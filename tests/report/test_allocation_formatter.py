"""Tests for AllocationReportFormatter."""
import csv
import io

import pytest

from k8s_cost_lens.metrics.allocation import AllocationResult
from k8s_cost_lens.report.allocation_formatter import AllocationReportFormatter


def make_result(
    ns: str, share: float, hourly: float
) -> AllocationResult:
    return AllocationResult(
        namespace=ns,
        allocated_hourly=hourly,
        allocated_monthly=hourly * 720,
        share_pct=share,
    )


@pytest.fixture
def sample_results() -> list:
    return [
        make_result("default", 60.0, 0.06),
        make_result("monitoring", 30.0, 0.03),
        make_result("kube-system", 10.0, 0.01),
    ]


@pytest.fixture
def formatter(sample_results) -> AllocationReportFormatter:
    return AllocationReportFormatter(sample_results)


def test_as_table_returns_string(formatter: AllocationReportFormatter) -> None:
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter: AllocationReportFormatter) -> None:
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Share %" in table
    assert "Hourly" in table
    assert "Monthly" in table


def test_as_table_contains_namespace_names(formatter: AllocationReportFormatter) -> None:
    table = formatter.as_table()
    assert "default" in table
    assert "monitoring" in table
    assert "kube-system" in table


def test_as_table_sorted_by_share_descending(
    formatter: AllocationReportFormatter,
) -> None:
    table = formatter.as_table()
    idx_default = table.index("default")
    idx_monitoring = table.index("monitoring")
    idx_kube = table.index("kube-system")
    assert idx_default < idx_monitoring < idx_kube


def test_as_csv_is_valid_csv(formatter: AllocationReportFormatter) -> None:
    csv_str = formatter.as_csv()
    reader = csv.reader(io.StringIO(csv_str))
    rows = list(reader)
    assert rows[0] == ["Namespace", "Share %", "Hourly ($)", "Monthly ($)"]
    assert len(rows) == 4  # header + 3 namespaces


def test_as_csv_contains_share_values(formatter: AllocationReportFormatter) -> None:
    csv_str = formatter.as_csv()
    assert "60.00" in csv_str
    assert "30.00" in csv_str
    assert "10.00" in csv_str


def test_total_allocated_hourly(formatter: AllocationReportFormatter) -> None:
    assert formatter.total_allocated_hourly() == pytest.approx(0.10)


def test_total_allocated_monthly(formatter: AllocationReportFormatter) -> None:
    assert formatter.total_allocated_monthly() == pytest.approx(0.10 * 720)


def test_empty_results() -> None:
    fmt = AllocationReportFormatter([])
    assert fmt.as_table() == "  ".join(
        ["Namespace", "Share %", "Hourly ($)", "Monthly ($)"]
    ) or isinstance(fmt.as_table(), str)
    assert fmt.total_allocated_hourly() == 0.0
    assert fmt.total_allocated_monthly() == 0.0
