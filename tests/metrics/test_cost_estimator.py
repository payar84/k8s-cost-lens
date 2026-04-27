"""Unit tests for the CostEstimator."""

import pytest

from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.cost_estimator import CostEstimator, NamespaceCost


@pytest.fixture
from k8s_cost_lens.metrics.cost_estimator import (
    DEFAULT_CPU_PRICE_PER_CORE_HOUR,
    DEFAULT_MEMORY_PRICE_PER_GB_HOUR,
)


def make_metrics(ns: str, cpu_cores: float, memory_bytes: float) -> NamespaceMetrics:
    m = NamespaceMetrics(namespace=ns)
    m.cpu_requests_cores = cpu_cores
    m.memory_requests_bytes = memory_bytes
    return m


def test_zero_resources():
    estimator = CostEstimator()
    result = estimator.estimate({"empty": make_metrics("empty", 0.0, 0.0)})
    assert result["empty"].total_cost_hourly == 0.0
    assert result["empty"].total_cost_monthly == 0.0


def test_cpu_only_cost():
    estimator = CostEstimator(cpu_price_per_core_hour=0.05, memory_price_per_gb_hour=0.0)
    result = estimator.estimate({"ns": make_metrics("ns", 2.0, 0.0)})
    assert result["ns"].cpu_cost_hourly == pytest.approx(0.10)
    assert result["ns"].memory_cost_hourly == 0.0


def test_memory_only_cost():
    gb = 1024 ** 3  # 1 GiB in bytes
    estimator = CostEstimator(cpu_price_per_core_hour=0.0, memory_price_per_gb_hour=0.006)
    result = estimator.estimate({"ns": make_metrics("ns", 0.0, 2 * gb)})
    assert result["ns"].memory_cost_hourly == pytest.approx(0.012)


def test_monthly_is_hourly_times_720():
    estimator = CostEstimator(cpu_price_per_core_hour=1.0, memory_price_per_gb_hour=0.0)
    result = estimator.estimate({"ns": make_metrics("ns", 1.0, 0.0)})
    assert result["ns"].total_cost_monthly == pytest.approx(720.0)


def test_multiple_namespaces():
    estimator = CostEstimator()
    metrics = {
        "default": make_metrics("default", 1.0, 512 * 1024 ** 2),
        "kube-system": make_metrics("kube-system", 0.5, 256 * 1024 ** 2),
    }
    result = estimator.estimate(metrics)
    assert set(result.keys()) == {"default", "kube-system"}
    assert result["default"].total_cost_hourly > result["kube-system"].total_cost_hourly


def test_returns_namespace_cost_type():
    estimator = CostEstimator()
    result = estimator.estimate({"ns": make_metrics("ns", 0.5, 0.0)})
    assert isinstance(result["ns"], NamespaceCost)
