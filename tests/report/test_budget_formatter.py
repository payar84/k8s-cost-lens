"""Tests for BudgetReportFormatter."""
import csv
import io

import pytest

from k8s_cost_lens.metrics.budget import BudgetStatus
from k8s_cost_lens.report.budget_formatter import BudgetReportFormatter


def make_status(
    namespace: str,
    hourly_cost: float = 0.01,
    hourly_limit: float | None = None,
    monthly_cost: float = 7.2,
    monthly_limit: float | None = None,
) -> BudgetStatus:
    hourly_pct = (hourly_cost / hourly_limit * 100) if hourly_limit else None
    monthly_pct = (monthly_cost / monthly_limit * 100) if monthly_limit else None
    hourly_exc = bool(hourly_limit and hourly_cost > hourly_limit)
    monthly_exc = bool(monthly_limit and monthly_cost > monthly_limit)
    return BudgetStatus(
        namespace=namespace,
        hourly_cost=hourly_cost,
        monthly_cost=monthly_cost,
        hourly_limit=hourly_limit,
        monthly_limit=monthly_limit,
        hourly_usage_pct=hourly_pct,
        monthly_usage_pct=monthly_pct,
        hourly_exceeded=hourly_exc,
        monthly_exceeded=monthly_exc,
    )


@pytest.fixture()
def sample_statuses():
    return [
        make_status("default", hourly_cost=0.005, hourly_limit=0.01, monthly_cost=3.6, monthly_limit=5.0),
        make_status("kube-system", hourly_cost=0.02, hourly_limit=0.01, monthly_cost=14.4, monthly_limit=10.0),
        make_status("monitoring"),
    ]


@pytest.fixture()
def formatter(sample_statuses):
    return BudgetReportFormatter(sample_statuses)


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Hourly" in table
    assert "Monthly" in table
    assert "Exceeded" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "default" in table
    assert "kube-system" in table
    assert "monitoring" in table


def test_exceeded_shown_as_yes(formatter):
    table = formatter.as_table()
    assert "YES" in table


def test_no_limit_shows_na(formatter):
    table = formatter.as_table()
    assert "N/A" in table


def test_exceeded_count(formatter):
    # kube-system exceeds both hourly and monthly
    assert formatter.exceeded_count() == 1


def test_exceeded_count_none_over():
    statuses = [make_status("ns1"), make_status("ns2")]
    fmt = BudgetReportFormatter(statuses)
    assert fmt.exceeded_count() == 0


def test_summary_line(formatter):
    line = formatter.summary_line()
    assert "1/3" in line
    assert "over budget" in line


def test_as_csv_is_parseable(formatter):
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    # header + 3 data rows
    assert len(rows) == 4
    assert rows[0][0] == "Namespace"


def test_as_csv_contains_all_namespaces(formatter):
    raw = formatter.as_csv()
    assert "default" in raw
    assert "kube-system" in raw
    assert "monitoring" in raw
