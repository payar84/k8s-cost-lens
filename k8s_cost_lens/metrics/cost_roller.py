"""Rolling window cost aggregation over a fixed number of recent snapshots."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional

from k8s_cost_lens.metrics.aggregator import AggregatedMetrics
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost, CostEstimator


@dataclass
class RollingWindow:
    """Maintains a bounded deque of AggregatedMetrics snapshots."""

    window_size: int
    _snapshots: deque = field(init=False)

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise ValueError("window_size must be >= 1")
        self._snapshots: deque[List[AggregatedMetrics]] = deque(maxlen=self.window_size)

    def push(self, snapshot: List[AggregatedMetrics]) -> None:
        """Add a new snapshot; oldest is evicted when the window is full."""
        self._snapshots.append(snapshot)

    @property
    def snapshots(self) -> List[List[AggregatedMetrics]]:
        return list(self._snapshots)

    @property
    def is_full(self) -> bool:
        return len(self._snapshots) == self.window_size

    def clear(self) -> None:
        self._snapshots.clear()


@dataclass
class RollingCost:
    namespace: str
    avg_hourly: float
    avg_monthly: float
    sample_count: int

    def __str__(self) -> str:
        return (
            f"{self.namespace}: avg_hourly=${self.avg_hourly:.4f} "
            f"avg_monthly=${self.avg_monthly:.2f} (n={self.sample_count})"
        )


class CostRoller:
    """Computes rolling-average costs across a sliding window of snapshots."""

    def __init__(self, estimator: CostEstimator, window_size: int = 5) -> None:
        self._estimator = estimator
        self._window = RollingWindow(window_size=window_size)

    @property
    def window_size(self) -> int:
        return self._window.window_size

    def push(self, snapshot: List[AggregatedMetrics]) -> None:
        self._window.push(snapshot)

    def rolling_costs(self) -> List[RollingCost]:
        """Return per-namespace rolling-average costs over the current window."""
        snapshots = self._window.snapshots
        if not snapshots:
            return []

        hourly_totals: dict[str, float] = {}
        monthly_totals: dict[str, float] = {}
        counts: dict[str, int] = {}

        for snapshot in snapshots:
            costs: List[NamespaceCost] = self._estimator.estimate(snapshot)
            for cost in costs:
                hourly_totals[cost.namespace] = hourly_totals.get(cost.namespace, 0.0) + cost.hourly_cost
                monthly_totals[cost.namespace] = monthly_totals.get(cost.namespace, 0.0) + cost.monthly_cost
                counts[cost.namespace] = counts.get(cost.namespace, 0) + 1

        return [
            RollingCost(
                namespace=ns,
                avg_hourly=hourly_totals[ns] / counts[ns],
                avg_monthly=monthly_totals[ns] / counts[ns],
                sample_count=counts[ns],
            )
            for ns in sorted(hourly_totals)
        ]
