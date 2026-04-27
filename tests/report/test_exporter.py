"""Tests for CostReportExporter."""

from __future__ import annotations

import json
import csv
import io
from pathlib import Path

import pytest

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost
from k8s_cost_lens.report.exporter import CostReportExporter


def make_cost(namespace: str, cpu: float, mem: float, hourly: float) -> NamespaceCost:
    return NamespaceCost(
        namespace=namespace,
        cpu_cores=cpu,
        memory_gib=mem,
        hourly_cost_usd=hourly,
        monthly_cost_usd=hourly * 720,
    )


@pytest.fixture()
def sample_costs() -> list[NamespaceCost]:
    return [
        make_cost("default", 1.0, 2.0, 0.05),
        make_cost("kube-system", 0.5, 1.0, 0.025),
    ]


@pytest.fixture()
def exporter(sample_costs) -> CostReportExporter:
    return CostReportExporter(sample_costs)


def test_to_string_json_is_valid_json(exporter):
    raw = exporter.to_string_json()
    data = json.loads(raw)
    assert "namespaces" in data


def test_to_string_json_contains_all_namespaces(exporter):
    data = json.loads(exporter.to_string_json())
    names = [r["namespace"] for r in data["namespaces"]]
    assert "default" in names
    assert "kube-system" in names


def test_to_string_json_record_fields(exporter):
    data = json.loads(exporter.to_string_json())
    record = data["namespaces"][0]
    for field in ("namespace", "cpu_cores", "memory_gib", "hourly_cost_usd", "monthly_cost_usd"):
        assert field in record, f"Missing field: {field}"


def test_to_file_csv_creates_file(tmp_path, exporter):
    dest = tmp_path / "report.csv"
    result = exporter.to_file_csv(dest)
    assert result == dest
    assert dest.exists()


def test_to_file_csv_content_has_header(tmp_path, exporter):
    dest = tmp_path / "report.csv"
    exporter.to_file_csv(dest)
    content = dest.read_text(encoding="utf-8")
    assert "namespace" in content.lower()


def test_to_file_json_creates_file(tmp_path, exporter):
    dest = tmp_path / "output" / "report.json"
    result = exporter.to_file_json(dest)
    assert result == dest
    assert dest.exists()


def test_to_file_json_valid_content(tmp_path, exporter):
    dest = tmp_path / "report.json"
    exporter.to_file_json(dest)
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert isinstance(data["namespaces"], list)
    assert len(data["namespaces"]) == 2


def test_monthly_cost_equals_hourly_times_720(exporter):
    data = json.loads(exporter.to_string_json())
    for record in data["namespaces"]:
        expected = round(record["hourly_cost_usd"] * 720, 4)
        assert abs(record["monthly_cost_usd"] - expected) < 1e-3
