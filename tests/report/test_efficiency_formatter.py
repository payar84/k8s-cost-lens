"""Tests for EfficiencyReportFormatter."""
import pytest
from k8s_cost_lens.metrics.cost_efficiency import EfficiencyScore
from k8s_cost_lens.report.efficiency_formatter import EfficiencyReportFormatter


def make_score(
    ns: str,
    cpu_eff: float = 0.8,
    mem_eff: float = 0.6,
    overall: float = 0.7,
) -> EfficiencyScore:
    return EfficiencyScore(
        namespace=ns,
        hourly_cost=0.05,
        cpu_requested=2.0,
        cpu_used=2.0 * cpu_eff,
        mem_requested_gb=4.0,
        mem_used_gb=4.0 * mem_eff,
        cpu_efficiency=cpu_eff,
        mem_efficiency=mem_eff,
        overall_efficiency=overall,
    )


@pytest.fixture
def sample_scores():
    return [make_score("alpha", 0.9, 0.7, 0.8), make_score("beta", 0.4, 0.3, 0.35)]


@pytest.fixture
def formatter(sample_scores):
    return EfficiencyReportFormatter(sample_scores)


def test_as_table_returns_string(formatter):
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_headers(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "CPU Eff" in table
    assert "Mem Eff" in table
    assert "Overall Eff" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "alpha" in table
    assert "beta" in table


def test_as_table_contains_percentages(formatter):
    table = formatter.as_table()
    assert "%" in table


def test_as_csv_returns_string(formatter):
    assert isinstance(formatter.as_csv(), str)


def test_as_csv_first_line_is_header(formatter):
    csv = formatter.as_csv()
    first = csv.splitlines()[0]
    assert "Namespace" in first
    assert "Overall Eff" in first


def test_as_csv_has_correct_row_count(formatter, sample_scores):
    csv = formatter.as_csv()
    lines = csv.splitlines()
    assert len(lines) == len(sample_scores) + 1  # header + data


def test_none_efficiency_renders_na():
    score = EfficiencyScore(
        namespace="ghost",
        hourly_cost=0.0,
        cpu_requested=0.0,
        cpu_used=0.0,
        mem_requested_gb=0.0,
        mem_used_gb=0.0,
        cpu_efficiency=None,
        mem_efficiency=None,
        overall_efficiency=None,
    )
    fmt = EfficiencyReportFormatter([score])
    table = fmt.as_table()
    assert "n/a" in table


def test_inefficiency_summary_identifies_worst(formatter):
    summary = formatter.inefficiency_summary()
    assert "beta" in summary  # beta has lower overall efficiency


def test_inefficiency_summary_no_data():
    score = EfficiencyScore(
        namespace="empty",
        hourly_cost=0.0,
        cpu_requested=0.0,
        cpu_used=0.0,
        mem_requested_gb=0.0,
        mem_used_gb=0.0,
        cpu_efficiency=None,
        mem_efficiency=None,
        overall_efficiency=None,
    )
    fmt = EfficiencyReportFormatter([score])
    assert "No efficiency data" in fmt.inefficiency_summary()
