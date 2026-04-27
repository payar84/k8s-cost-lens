"""Tests for CostReportFormatter."""

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.report.formatter import CostReportFormatter


def make_cost(namespace: str, cpu: float, mem_bytes: float,
              hourly: float, monthly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_cores=cpu,
        memory_bytes=mem_bytes,
        hourly_cost=hourly,
        monthly_cost=monthly,
    )


@pytest.fixture
def formatter():
    return CostReportFormatter()


@pytest.fixture
def sample_costs():
    return [
        make_cost("default", 2.0, 4 * 1024 ** 3, 0.10, 72.0),
        make_cost("kube-system", 0.5, 1 * 1024 ** 3, 0.02, 14.4),
    ]


def test_as_table_contains_headers(formatter, sample_costs):
    table = formatter.as_table(sample_costs)
    assert "NAMESPACE" in table
    assert "CPU (cores)" in table
    assert "MONTHLY ($)" in table


def test_as_table_contains_namespace_names(formatter, sample_costs):
    table = formatter.as_table(sample_costs)
    assert "default" in table
    assert "kube-system" in table


def test_as_table_sorted_by_monthly_cost_descending(formatter, sample_costs):
    table = formatter.as_table(sample_costs)
    idx_default = table.index("default")
    idx_kube = table.index("kube-system")
    assert idx_default < idx_kube  # higher cost namespace appears first


def test_as_table_includes_total_row(formatter, sample_costs):
    table = formatter.as_table(sample_costs)
    assert "TOTAL" in table


def test_as_table_empty_input(formatter):
    result = formatter.as_table([])
    assert "No namespace cost data available." in result


def test_as_csv_header_row(formatter, sample_costs):
    csv = formatter.as_csv(sample_costs)
    first_line = csv.splitlines()[0]
    assert first_line == "namespace,cpu_cores,memory_gib,hourly_cost,monthly_cost"


def test_as_csv_row_count(formatter, sample_costs):
    csv = formatter.as_csv(sample_costs)
    lines = csv.splitlines()
    # 1 header + 2 data rows
    assert len(lines) == 3


def test_as_csv_values(formatter):
    costs = [make_cost("prod", 1.0, 2 * 1024 ** 3, 0.05, 36.0)]
    csv = formatter.as_csv(costs)
    data_line = csv.splitlines()[1]
    assert data_line.startswith("prod,")
    assert "36.00" in data_line
