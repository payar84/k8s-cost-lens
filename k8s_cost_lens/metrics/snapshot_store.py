"""Persistent in-memory snapshot store with optional size cap."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, List, Optional

from k8s_cost_lens.metrics.collector import NamespaceMetrics


@dataclass
class TimestampedSnapshot:
    """A set of namespace metrics captured at a specific point in time."""

    captured_at: datetime
    metrics: List[NamespaceMetrics]


class SnapshotStore:
    """Stores a bounded history of metric snapshots.

    Parameters
    ----------
    max_snapshots:
        Maximum number of snapshots to retain.  Oldest entries are evicted
        automatically once the cap is reached.  ``None`` means unlimited.
    """

    def __init__(self, max_snapshots: Optional[int] = 100) -> None:
        self._max = max_snapshots
        self._store: Deque[TimestampedSnapshot] = deque(
            maxlen=max_snapshots if max_snapshots and max_snapshots > 0 else None
        )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def push(self, metrics: List[NamespaceMetrics]) -> TimestampedSnapshot:
        """Record *metrics* with the current UTC timestamp and return the entry."""
        entry = TimestampedSnapshot(
            captured_at=datetime.now(tz=timezone.utc),
            metrics=list(metrics),
        )
        self._store.append(entry)
        return entry

    def clear(self) -> None:
        """Remove all stored snapshots."""
        self._store.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def all(self) -> List[TimestampedSnapshot]:
        """Return all snapshots in chronological order (oldest first)."""
        return list(self._store)

    def latest(self) -> Optional[TimestampedSnapshot]:
        """Return the most-recently pushed snapshot, or ``None`` if empty."""
        return self._store[-1] if self._store else None

    def __len__(self) -> int:  # pragma: no cover
        return len(self._store)
