"""Tests for CapReportFormatter."""
from __future__ import annotations

import csv
import io

import pytest

from k8s_cost_lens.metrics.cost_cap import CapViolation
from k8s_cost_lens.report.cap_formatter import CapReportFormatter


def make_violation(
    namespace: str = "prod",
    actual_hourly: float = 2.0,
    cap_hourly: float = 1.0,
    actual_monthly: float = 1440.0,
    cap_monthly: float = 720.0,
) -> CapViolation:
    return CapViolation(
        namespace=namespace,
        cap_hourly=cap_hourly,
        cap_monthly=cap_monthly,
        actual_hourly=actual_hourly,
        actual_monthly=actual_monthly,
    )


@pytest.fixture
def sample_violations():
    return [make_violation("prod"), make_violation("staging", 0.5, 1.0, 360.0, 500.0)]


@pytest.fixture
def formatter(sample_violations):
    return CapReportFormatter(sample_violations)


def test_as_table_returns_string(formatter):
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Actual Hourly" in table
    assert "Cap Monthly" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "prod" in table
    assert "staging" in table


def test_as_table_shows_yes_for_exceeded(formatter):
    table = formatter.as_table()
    assert "YES" in table


def test_empty_violations_returns_no_violations_message():
    f = CapReportFormatter([])
    assert "No cost-cap violations" in f.as_table()


def test_as_csv_is_parseable(formatter):
    csv_output = formatter.as_csv()
    reader = csv.reader(io.StringIO(csv_output))
    rows = list(reader)
    assert rows[0][0] == "Namespace"
    assert len(rows) == 3  # header + 2 violations


def test_as_csv_contains_namespace(formatter):
    assert "prod" in formatter.as_csv()


def test_violation_count(formatter):
    assert formatter.violation_count() == 2


def test_summary_line_plural(formatter):
    assert "2 cap violations" in formatter.summary_line()


def test_summary_line_singular():
    f = CapReportFormatter([make_violation()])
    assert "1 cap violation detected" in f.summary_line()
    assert "violations" not in f.summary_line()
