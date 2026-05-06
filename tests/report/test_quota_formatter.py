"""Tests for QuotaReportFormatter."""
import pytest
from k8s_cost_lens.metrics.cost_quota import QuotaResult
from k8s_cost_lens.report.quota_formatter import QuotaReportFormatter


def make_result(
    namespace: str,
    hourly: float,
    soft_h: float | None = None,
    hard_h: float | None = None,
    soft_m: float | None = None,
    hard_m: float | None = None,
) -> QuotaResult:
    return QuotaResult(
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
        soft_hourly_limit=soft_h,
        hard_hourly_limit=hard_h,
        soft_monthly_limit=soft_m,
        hard_monthly_limit=hard_m,
    )


@pytest.fixture
def sample_results() -> list[QuotaResult]:
    return [
        make_result("team-a", 0.05, soft_h=0.10, hard_h=0.20),
        make_result("team-b", 0.25, soft_h=0.10, hard_h=0.20),
        make_result("team-c", 0.12, soft_h=0.10, hard_h=0.20),
        make_result("team-d", 0.01),
    ]


@pytest.fixture
def formatter(sample_results) -> QuotaReportFormatter:
    return QuotaReportFormatter(sample_results)


def test_as_table_returns_string(formatter):
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Severity" in table
    assert "Hourly" in table
    assert "Monthly" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "team-a" in table
    assert "team-b" in table
    assert "team-d" in table


def test_as_table_shows_severity(formatter):
    table = formatter.as_table()
    assert "HARD" in table
    assert "SOFT" in table
    assert "OK" in table


def test_as_csv_returns_string(formatter):
    assert isinstance(formatter.as_csv(), str)


def test_as_csv_first_line_is_header(formatter):
    csv = formatter.as_csv()
    first = csv.splitlines()[0]
    assert "namespace" in first
    assert "severity" in first


def test_as_csv_contains_all_namespaces(formatter, sample_results):
    csv = formatter.as_csv()
    for r in sample_results:
        assert r.namespace in csv


def test_breached_count(formatter):
    # team-b: hard, team-c: soft => 2 breached
    assert formatter.breached_count() == 2


def test_summary_line_contains_counts(formatter):
    line = formatter.summary_line()
    assert "4" in line   # total namespaces
    assert "2" in line   # breached


def test_no_limits_all_ok():
    results = [
        make_result("ns-x", 5.0),
        make_result("ns-y", 10.0),
    ]
    fmt = QuotaReportFormatter(results)
    assert fmt.breached_count() == 0
    assert "0 breached" in fmt.summary_line()
