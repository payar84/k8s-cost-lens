"""Tests for BaselineComparisonFormatter."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.cost_baseline import BaselineDiff
from k8s_cost_lens.report.baseline_formatter import BaselineComparisonFormatter


def make_diff(
    namespace: str,
    baseline_hourly: float,
    current_hourly: float,
) -> BaselineDiff:
    return BaselineDiff(
        namespace=namespace,
        baseline_hourly=baseline_hourly,
        current_hourly=current_hourly,
        baseline_monthly=baseline_hourly * 720,
        current_monthly=current_hourly * 720,
    )


@pytest.fixture
def sample_diffs():
    return [
        make_diff("ns-a", 1.0, 1.5),
        make_diff("ns-b", 2.0, 2.0),
        make_diff("ns-c", 0.0, 0.5),
    ]


@pytest.fixture
def formatter(sample_diffs):
    return BaselineComparisonFormatter("v1", sample_diffs)


def test_as_table_returns_string(formatter):
    result = formatter.as_table()
    assert isinstance(result, str)


def test_as_table_contains_baseline_name(formatter):
    assert "v1" in formatter.as_table()


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "% Change" in table
    assert "Δ $/hr" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "ns-a" in table
    assert "ns-b" in table
    assert "ns-c" in table


def test_positive_delta_has_plus_sign(formatter):
    table = formatter.as_table()
    assert "+$" in table


def test_pct_change_none_shows_na(sample_diffs):
    fmt = BaselineComparisonFormatter("v1", sample_diffs)
    table = fmt.as_table()
    # ns-c has baseline_hourly=0 so pct_change is None
    assert "n/a" in table


def test_as_csv_returns_string(formatter):
    result = formatter.as_csv()
    assert isinstance(result, str)


def test_as_csv_has_header_row(formatter):
    lines = formatter.as_csv().splitlines()
    assert lines[0].startswith("namespace,")


def test_as_csv_row_count(formatter, sample_diffs):
    lines = formatter.as_csv().splitlines()
    # header + one row per diff
    assert len(lines) == len(sample_diffs) + 1


def test_as_csv_empty_pct_when_baseline_zero(sample_diffs):
    fmt = BaselineComparisonFormatter("v1", sample_diffs)
    csv = fmt.as_csv()
    # ns-c row: pct_change column should be empty string between commas
    ns_c_row = next(r for r in csv.splitlines() if r.startswith("ns-c"))
    parts = ns_c_row.split(",")
    assert parts[3] == "0.500000"  # delta
    assert parts[4] == ""          # empty pct


def test_as_csv_namespaces_sorted(formatter):
    lines = formatter.as_csv().splitlines()[1:]  # skip header
    namespaces = [l.split(",")[0] for l in lines]
    assert namespaces == sorted(namespaces)
