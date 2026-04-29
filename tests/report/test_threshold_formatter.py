"""Tests for ThresholdReportFormatter."""
from __future__ import annotations

import csv
import io
from typing import List

import pytest

from k8s_cost_lens.metrics.threshold import ThresholdViolation
from k8s_cost_lens.report.threshold_formatter import ThresholdReportFormatter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_violation(
    namespace: str = "default",
    violation_type: str = "hourly",
    limit: float = 1.0,
    actual: float = 2.0,
) -> ThresholdViolation:
    v = ThresholdViolation(namespace=namespace, violation_type=violation_type, limit=limit, actual=actual)
    return v


@pytest.fixture()
def sample_violations() -> List[ThresholdViolation]:
    return [
        make_violation("ns-a", "hourly", limit=0.5, actual=0.9),
        make_violation("ns-b", "monthly", limit=200.0, actual=350.0),
        make_violation("ns-a", "monthly", limit=300.0, actual=600.0),
    ]


@pytest.fixture()
def formatter(sample_violations: List[ThresholdViolation]) -> ThresholdReportFormatter:
    return ThresholdReportFormatter(sample_violations)


# ---------------------------------------------------------------------------
# as_table tests
# ---------------------------------------------------------------------------

def test_as_table_contains_header(formatter: ThresholdReportFormatter) -> None:
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Type" in table
    assert "Limit" in table
    assert "Actual" in table


def test_as_table_contains_namespace_names(formatter: ThresholdReportFormatter) -> None:
    table = formatter.as_table()
    assert "ns-a" in table
    assert "ns-b" in table


def test_as_table_contains_violation_types(formatter: ThresholdReportFormatter) -> None:
    table = formatter.as_table()
    assert "hourly" in table
    assert "monthly" in table


def test_as_table_empty_returns_no_violations_message() -> None:
    fmt = ThresholdReportFormatter([])
    assert fmt.as_table() == "No threshold violations detected."


# ---------------------------------------------------------------------------
# as_csv tests
# ---------------------------------------------------------------------------

def test_as_csv_is_valid_csv(formatter: ThresholdReportFormatter) -> None:
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    # header + 3 data rows
    assert len(rows) == 4


def test_as_csv_header_row(formatter: ThresholdReportFormatter) -> None:
    raw = formatter.as_csv()
    first_line = raw.splitlines()[0]
    assert "Namespace" in first_line
    assert "Limit" in first_line


# ---------------------------------------------------------------------------
# violation_count / summary_line tests
# ---------------------------------------------------------------------------

def test_violation_count(formatter: ThresholdReportFormatter) -> None:
    assert formatter.violation_count() == 3


def test_violation_count_empty() -> None:
    assert ThresholdReportFormatter([]).violation_count() == 0


def test_summary_line_with_violations(formatter: ThresholdReportFormatter) -> None:
    summary = formatter.summary_line()
    assert "3" in summary
    assert "violation" in summary


def test_summary_line_no_violations() -> None:
    summary = ThresholdReportFormatter([]).summary_line()
    assert "within" in summary.lower()
