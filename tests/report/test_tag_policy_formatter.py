"""Tests for TagPolicyReportFormatter."""
import csv
import io

import pytest

from k8s_cost_lens.metrics.tag_policy import PolicyViolation
from k8s_cost_lens.report.tag_policy_formatter import TagPolicyReportFormatter


def make_violation(
    namespace: str,
    missing: list[str] | None = None,
    invalid: dict | None = None,
) -> PolicyViolation:
    return PolicyViolation(
        namespace=namespace,
        missing_tags=missing or [],
        invalid_tags=invalid or {},
    )


@pytest.fixture
def sample_violations() -> list[PolicyViolation]:
    return [
        make_violation("ns-a", missing=["team", "env"]),
        make_violation("ns-b", invalid={"env": "'qa' not in allowed ['prod', 'dev']"}),
        make_violation("ns-c", missing=["team"], invalid={"env": "bad"}),
    ]


@pytest.fixture
def formatter(sample_violations) -> TagPolicyReportFormatter:
    return TagPolicyReportFormatter(sample_violations)


def test_as_table_returns_string(formatter):
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Missing Labels" in table
    assert "Invalid Labels" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "ns-a" in table
    assert "ns-b" in table
    assert "ns-c" in table


def test_as_table_empty_violations():
    fmt = TagPolicyReportFormatter([])
    result = fmt.as_table()
    assert "No tag policy violations" in result


def test_as_csv_is_parseable(formatter):
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    assert rows[0] == ["Namespace", "Missing Labels", "Invalid Labels", "Compliant"]
    assert len(rows) == 4  # header + 3 violations


def test_as_csv_compliant_column_is_no(formatter):
    raw = formatter.as_csv()
    reader = csv.reader(io.StringIO(raw))
    data_rows = list(reader)[1:]
    for row in data_rows:
        assert row[3] == "No"


def test_violation_count(formatter):
    assert formatter.violation_count() == 3


def test_violation_count_empty():
    assert TagPolicyReportFormatter([]).violation_count() == 0


def test_summary_line_with_violations(formatter):
    line = formatter.summary_line()
    assert "3" in line
    assert "violate" in line


def test_summary_line_no_violations():
    line = TagPolicyReportFormatter([]).summary_line()
    assert "compliant" in line.lower()
