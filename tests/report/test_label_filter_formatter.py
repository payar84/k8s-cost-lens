"""Tests for LabelFilterReportFormatter."""
import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.metrics.label_filter import LabelSelector
from k8s_cost_lens.report.label_filter_formatter import LabelFilterReportFormatter


LABEL_MAP = {
    "team-alpha": {"team": "alpha", "env": "prod"},
    "team-beta": {"team": "beta", "env": "prod"},
    "team-gamma": {"team": "gamma", "env": "staging"},
}


def make_cost(namespace: str, cpu: float = 0.02, mem: float = 0.01) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_cost_hourly=cpu,
        memory_cost_hourly=mem,
        total_hourly=cpu + mem,
        total_monthly=(cpu + mem) * 720,
    )


@pytest.fixture()
def sample_costs():
    return [make_cost(ns) for ns in ["team-alpha", "team-beta"]]


@pytest.fixture()
def formatter(sample_costs):
    sel = LabelSelector.from_string("env=prod")
    return LabelFilterReportFormatter(sample_costs, sel, LABEL_MAP)


def test_as_table_returns_string(formatter):
    assert isinstance(formatter.as_table(), str)


def test_as_table_contains_selector_info(formatter):
    table = formatter.as_table()
    assert "env=prod" in table


def test_as_table_contains_matching_count(formatter):
    table = formatter.as_table()
    assert "Matching namespaces: 2" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "team-alpha" in table
    assert "team-beta" in table


def test_as_table_contains_label_columns(formatter):
    table = formatter.as_table()
    assert "env" in table
    assert "team" in table


def test_as_table_empty_selector_shows_none():
    costs = [make_cost("team-alpha")]
    sel = LabelSelector()
    fmt = LabelFilterReportFormatter(costs, sel, LABEL_MAP)
    assert "<none>" in fmt.as_table()


def test_as_csv_returns_string(formatter):
    assert isinstance(formatter.as_csv(), str)


def test_as_csv_first_line_is_header(formatter):
    lines = formatter.as_csv().splitlines()
    assert lines[0].startswith("namespace")


def test_as_csv_contains_label_keys(formatter):
    csv = formatter.as_csv()
    assert "env" in csv
    assert "team" in csv


def test_as_csv_row_count_matches_costs(formatter, sample_costs):
    lines = formatter.as_csv().splitlines()
    # header + one row per cost
    assert len(lines) == 1 + len(sample_costs)


def test_as_csv_contains_namespace_values(formatter):
    csv = formatter.as_csv()
    assert "team-alpha" in csv
    assert "team-beta" in csv
