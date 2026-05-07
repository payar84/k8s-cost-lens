"""Tests for TopNReportFormatter."""
import pytest

from k8s_cost_lens.metrics.cost_topn import TopNResult
from k8s_cost_lens.report.topn_formatter import TopNReportFormatter


def make_result(rank: int, namespace: str, hourly: float) -> TopNResult:
    return TopNResult(
        rank=rank,
        namespace=namespace,
        hourly_cost=hourly,
        monthly_cost=hourly * 720,
    )


@pytest.fixture()
def sample_results():
    return [
        make_result(1, "ns-e", 0.80),
        make_result(2, "ns-b", 0.50),
        make_result(3, "ns-c", 0.30),
    ]


@pytest.fixture()
def formatter(sample_results):
    return TopNReportFormatter(sample_results)


def test_as_table_returns_string(formatter):
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Rank" in table
    assert "Namespace" in table
    assert "Hourly" in table
    assert "Monthly" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "ns-e" in table
    assert "ns-b" in table
    assert "ns-c" in table


def test_as_table_contains_ranks(formatter):
    table = formatter.as_table()
    assert "1" in table
    assert "2" in table
    assert "3" in table


def test_as_csv_returns_string(formatter):
    assert isinstance(formatter.as_csv(), str)


def test_as_csv_first_line_is_header(formatter):
    csv = formatter.as_csv()
    first_line = csv.splitlines()[0]
    assert "Rank" in first_line
    assert "Namespace" in first_line


def test_as_csv_row_count(formatter, sample_results):
    csv = formatter.as_csv()
    lines = csv.splitlines()
    # header + one row per result
    assert len(lines) == len(sample_results) + 1


def test_as_csv_contains_namespace(formatter):
    csv = formatter.as_csv()
    assert "ns-e" in csv


def test_summary_line_mentions_count(formatter):
    line = formatter.summary_line()
    assert "3" in line


def test_empty_formatter_as_table():
    f = TopNReportFormatter([])
    table = f.as_table()
    assert isinstance(table, str)


def test_empty_formatter_summary():
    f = TopNReportFormatter([])
    assert "0" in f.summary_line()
