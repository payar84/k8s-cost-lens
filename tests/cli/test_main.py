"""Tests for the CLI entry point."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from k8s_cost_lens.cli.main import build_parser, run
from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


SAMPLE_METRICS = [
    NamespaceMetrics(namespace="default", cpu_cores=0.5, memory_gib=1.0),
    NamespaceMetrics(namespace="kube-system", cpu_cores=0.2, memory_gib=0.5),
]


@pytest.fixture()
def mock_collector():
    with patch("k8s_cost_lens.cli.main.MetricsCollector") as cls:
        instance = MagicMock()
        instance.collect.return_value = SAMPLE_METRICS
        cls.return_value = instance
        yield cls


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.cpu_price == pytest.approx(0.048)
    assert args.mem_price == pytest.approx(0.006)
    assert args.kubeconfig is None
    assert args.csv is None
    assert args.json is None


def test_build_parser_custom_prices():
    parser = build_parser()
    args = parser.parse_args(["--cpu-price", "0.1", "--mem-price", "0.01"])
    assert args.cpu_price == pytest.approx(0.1)
    assert args.mem_price == pytest.approx(0.01)


def test_csv_and_json_are_mutually_exclusive():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--csv", "out.csv", "--json", "out.json"])


def test_run_stdout(mock_collector, capsys):
    exit_code = run([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "default" in captured.out
    assert "kube-system" in captured.out


def test_run_csv_output(mock_collector, tmp_path):
    csv_file = tmp_path / "report.csv"
    exit_code = run(["--csv", str(csv_file)])
    assert exit_code == 0
    assert csv_file.exists()
    content = csv_file.read_text()
    assert "default" in content
    assert "kube-system" in content


def test_run_json_output(mock_collector, tmp_path):
    json_file = tmp_path / "report.json"
    exit_code = run(["--json", str(json_file)])
    assert exit_code == 0
    assert json_file.exists()
    data = json.loads(json_file.read_text())
    namespaces = [entry["namespace"] for entry in data]
    assert "default" in namespaces
    assert "kube-system" in namespaces


def test_run_passes_kubeconfig(mock_collector):
    run(["--kubeconfig", "/tmp/my.kubeconfig"])
    mock_collector.assert_called_once_with(kubeconfig="/tmp/my.kubeconfig")
