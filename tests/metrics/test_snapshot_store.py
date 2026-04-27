"""Tests for SnapshotStore."""
from __future__ import annotations

from datetime import timezone
from unittest.mock import patch

import pytest

from k8s_cost_lens.metrics.collector import NamespaceMetrics
from k8s_cost_lens.metrics.snapshot_store import SnapshotStore


def make_nm(namespace: str, cpu: float = 0.5, mem: float = 512.0) -> NamespaceMetrics:
    return NamespaceMetrics(namespace=namespace, cpu_cores=cpu, memory_mib=mem)


@pytest.fixture()
def store() -> SnapshotStore:
    return SnapshotStore(max_snapshots=5)


def test_empty_store_latest_is_none(store: SnapshotStore) -> None:
    assert store.latest() is None


def test_empty_store_all_returns_empty(store: SnapshotStore) -> None:
    assert store.all() == []


def test_push_returns_timestamped_snapshot(store: SnapshotStore) -> None:
    metrics = [make_nm("default")]
    entry = store.push(metrics)
    assert entry.metrics == metrics
    assert entry.captured_at.tzinfo == timezone.utc


def test_push_increments_length(store: SnapshotStore) -> None:
    store.push([make_nm("a")])
    store.push([make_nm("b")])
    assert len(store) == 2


def test_latest_returns_most_recent(store: SnapshotStore) -> None:
    store.push([make_nm("first")])
    store.push([make_nm("second")])
    latest = store.latest()
    assert latest is not None
    assert latest.metrics[0].namespace == "second"


def test_all_returns_chronological_order(store: SnapshotStore) -> None:
    for ns in ("a", "b", "c"):
        store.push([make_nm(ns)])
    names = [s.metrics[0].namespace for s in store.all()]
    assert names == ["a", "b", "c"]


def test_max_snapshots_evicts_oldest() -> None:
    store = SnapshotStore(max_snapshots=3)
    for ns in ("a", "b", "c", "d"):
        store.push([make_nm(ns)])
    names = [s.metrics[0].namespace for s in store.all()]
    assert names == ["b", "c", "d"]
    assert len(store) == 3


def test_clear_removes_all_entries(store: SnapshotStore) -> None:
    store.push([make_nm("x")])
    store.clear()
    assert store.latest() is None
    assert len(store) == 0


def test_unlimited_store_grows_beyond_default() -> None:
    store = SnapshotStore(max_snapshots=None)
    for i in range(200):
        store.push([make_nm(f"ns-{i}")])
    assert len(store) == 200
