"""Tests for AnomalyReportFormatter."""
from __future__ import annotations

import pytest

from k8s_cost_lens.metrics.anomaly import AnomalyResult
from k8s_cost_lens.report.anomaly_formatter import AnomalyReportFormatter


def make_result(
    namespace: str,
    hourly: float,
    mean: float = 1.0,
    stddev: float = 0.5,
    z_score: float | None = 0.0,
    is_anomaly: bool = False,
) -> AnomalyResult:
    return AnomalyResult(
        namespace=namespace,
        hourly_cost=hourly,
        mean_hourly=mean,
        stddev_hourly=stddev,
        z_score=z_score,
        is_anomaly=is_anomaly,
    )


@pytest.fixture
def sample_results() -> list[AnomalyResult]:
    return [
        make_result("default", 0.5, z_score=0.1),
        make_result("kube-system", 5.0, z_score=2.5, is_anomaly=True),
        make_result("monitoring", 0.8, z_score=None),
    ]


@pytest.fixture
def formatter(sample_results) -> AnomalyReportFormatter:
    return AnomalyReportFormatter(results=sample_results)


def test_as_table_contains_header(formatter):
    table = formatter.as_table()
    assert "Namespace" in table
    assert "Hourly" in table
    assert "Z-Score" in table


def test_as_table_contains_namespace_names(formatter):
    table = formatter.as_table()
    assert "default" in table
    assert "kube-system" in table
    assert "monitoring" in table


def test_as_table_marks_anomaly(formatter):
    table = formatter.as_table()
    assert "ANOMALY" in table
    assert "OK" in table


def test_as_table_empty_returns_message():
    f = AnomalyReportFormatter(results=[])
    assert "No anomaly data" in f.as_table()


def test_as_csv_has_header(formatter):
    csv = formatter.as_csv()
    first_line = csv.splitlines()[0]
    assert "namespace" in first_line
    assert "z_score" in first_line


def test_as_csv_row_count(formatter, sample_results):
    csv = formatter.as_csv()
    # header + one row per result
    assert len(csv.splitlines()) == len(sample_results) + 1


def test_as_csv_handles_none_z_score(formatter):
    csv = formatter.as_csv()
    # monitoring has z_score=None -> empty field between commas
    lines = {l.split(",")[0]: l for l in csv.splitlines()[1:]}
    monitoring_line = lines["monitoring"]
    parts = monitoring_line.split(",")
    assert parts[4] == ""  # z_score column empty


def test_anomaly_count(formatter):
    assert formatter.anomaly_count() == 1


def test_summary_line(formatter):
    summary = formatter.summary_line()
    assert "1/3" in summary
    assert "flagged" in summary
