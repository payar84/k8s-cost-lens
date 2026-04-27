"""Unit tests for CPU and memory string parsing helpers in collector."""

import pytest

from k8s_cost_lens.metrics.collector import _parse_cpu, _parse_memory


# --- CPU parsing ---

@pytest.mark.parametrize("value,expected", [
    ("1", 1.0),
    ("2", 2.0),
    ("500m", 0.5),
    ("250m", 0.25),
    ("1000m", 1.0),
    ("100m", 0.1),
])
def test_parse_cpu(value, expected):
    assert _parse_cpu(value) == pytest.approx(expected)


# --- Memory parsing ---

@pytest.mark.parametrize("value,expected", [
    ("1024", 1024.0),
    ("1Ki", 1024.0),
    ("1Mi", 1024 ** 2),
    ("1Gi", 1024 ** 3),
    ("512Mi", 512 * 1024 ** 2),
    ("2Gi", 2 * 1024 ** 3),
    ("1K", 1000.0),
    ("1M", 1_000_000.0),
    ("1G", 1_000_000_000.0),
])
def test_parse_memory(value, expected):
    assert _parse_memory(value) == pytest.approx(expected)


def test_parse_cpu_zero_millis():
    assert _parse_cpu("0m") == 0.0


def test_parse_memory_zero():
    assert _parse_memory("0") == 0.0
