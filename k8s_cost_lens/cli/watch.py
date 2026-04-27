"""Continuous watch mode: poll metrics on an interval, store snapshots."""
from __future__ import annotations

import time
from typing import Callable, Optional

from k8s_cost_lens.metrics.collector import MetricsCollector
from k8s_cost_lens.metrics.snapshot_store import SnapshotStore, TimestampedSnapshot
from k8s_cost_lens.report.exporter import CostReportExporter
from k8s_cost_lens.metrics.cost_estimator import CostEstimator


class WatchLoop:
    """Poll the cluster at *interval_seconds* and persist snapshots.

    Parameters
    ----------
    collector:
        Source of live ``NamespaceMetrics``.
    estimator:
        Converts metrics to cost figures.
    store:
        Destination for each captured snapshot.
    interval_seconds:
        Seconds to sleep between polls.
    on_snapshot:
        Optional callback invoked with each ``TimestampedSnapshot`` after it
        is stored.  Useful for streaming output during watch mode.
    """

    def __init__(
        self,
        collector: MetricsCollector,
        estimator: CostEstimator,
        store: SnapshotStore,
        interval_seconds: float = 30.0,
        on_snapshot: Optional[Callable[[TimestampedSnapshot], None]] = None,
    ) -> None:
        self._collector = collector
        self._estimator = estimator
        self._store = store
        self._interval = interval_seconds
        self._on_snapshot = on_snapshot
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_once(self) -> TimestampedSnapshot:
        """Collect metrics, store a snapshot, invoke callback, and return it."""
        metrics = self._collector.collect()
        entry = self._store.push(metrics)
        if self._on_snapshot:
            self._on_snapshot(entry)
        return entry

    def run(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll until interrupted or *max_iterations* is reached."""
        self._running = True
        iteration = 0
        try:
            while self._running:
                self.run_once()
                iteration += 1
                if max_iterations is not None and iteration >= max_iterations:
                    break
                time.sleep(self._interval)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False

    def stop(self) -> None:  # pragma: no cover
        """Signal the run-loop to exit after the current iteration."""
        self._running = False
