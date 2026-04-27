"""Tests for WatchLoop."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.snapshot_store import SnapshotStore
from k8s_cost_lens.metrics.cost_estimator import CostEstimator
from k8s_cost_lens.cli.watch import WatchLoop


def _make_collector(namespaces=("default", "kube-system")) -> MagicMock:
    collector = MagicMock()
    collector.collect.return_value = [
        NamespaceMetrics(namespace=ns, cpu_cores=0.1, memory_mib=128.0)
        for ns in namespaces
    ]
    return collector


@pytest.fixture()
def store() -> SnapshotStore:
    return SnapshotStore(max_snapshots=50)


@pytest.fixture()
def estimator() -> MagicMock:
    return MagicMock(spec=CostEstimator)


def test_run_once_stores_snapshot(store: SnapshotStore, estimator: MagicMock) -> None:
    loop = WatchLoop(_make_collector(), estimator, store)
    loop.run_once()
    assert len(store) == 1


def test_run_once_returns_snapshot(store: SnapshotStore, estimator: MagicMock) -> None:
    loop = WatchLoop(_make_collector(), estimator, store)
    entry = loop.run_once()
    assert entry is store.latest()


def test_run_once_calls_on_snapshot(store: SnapshotStore, estimator: MagicMock) -> None:
    callback = MagicMock()
    loop = WatchLoop(_make_collector(), estimator, store, on_snapshot=callback)
    entry = loop.run_once()
    callback.assert_called_once_with(entry)


def test_run_max_iterations(store: SnapshotStore, estimator: MagicMock) -> None:
    with patch("k8s_cost_lens.cli.watch.time.sleep"):
        loop = WatchLoop(_make_collector(), estimator, store, interval_seconds=0)
        loop.run(max_iterations=4)
    assert len(store) == 4


def test_run_sleeps_between_polls(store: SnapshotStore, estimator: MagicMock) -> None:
    with patch("k8s_cost_lens.cli.watch.time.sleep") as mock_sleep:
        loop = WatchLoop(_make_collector(), estimator, store, interval_seconds=15)
        loop.run(max_iterations=3)
    assert mock_sleep.call_count == 2  # no sleep after last iteration
    mock_sleep.assert_called_with(15)


def test_snapshot_contains_correct_metrics(store: SnapshotStore, estimator: MagicMock) -> None:
    collector = _make_collector(namespaces=("prod",))
    loop = WatchLoop(collector, estimator, store)
    entry = loop.run_once()
    assert len(entry.metrics) == 1
    assert entry.metrics[0].namespace == "prod"
