"""Cluster-wide cost summary aggregation across all namespaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class ClusterCostSummary:
    """Aggregated cost figures for the entire cluster."""

    total_hourly: float
    total_monthly: float
    namespace_count: int
    avg_hourly_per_namespace: float
    avg_monthly_per_namespace: float
    max_hourly_namespace: Optional[str]
    max_hourly_cost: float
    min_hourly_namespace: Optional[str]
    min_hourly_cost: float

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"ClusterCostSummary(namespaces={self.namespace_count}, "
            f"total_hourly=${self.total_hourly:.4f}, "
            f"total_monthly=${self.total_monthly:.2f})"
        )


class ClusterCostSummarizer:
    """Computes a cluster-wide rollup from per-namespace cost estimates."""

    def summarize(self, costs: List[NamespaceCost]) -> ClusterCostSummary:
        """Return a :class:`ClusterCostSummary` for *costs*.

        An empty list is valid and returns a zero-valued summary.
        """
        if not costs:
            return ClusterCostSummary(
                total_hourly=0.0,
                total_monthly=0.0,
                namespace_count=0,
                avg_hourly_per_namespace=0.0,
                avg_monthly_per_namespace=0.0,
                max_hourly_namespace=None,
                max_hourly_cost=0.0,
                min_hourly_namespace=None,
                min_hourly_cost=0.0,
            )

        total_hourly = sum(c.hourly_cost for c in costs)
        total_monthly = sum(c.monthly_cost for c in costs)
        n = len(costs)

        max_entry = max(costs, key=lambda c: c.hourly_cost)
        min_entry = min(costs, key=lambda c: c.hourly_cost)

        return ClusterCostSummary(
            total_hourly=total_hourly,
            total_monthly=total_monthly,
            namespace_count=n,
            avg_hourly_per_namespace=total_hourly / n,
            avg_monthly_per_namespace=total_monthly / n,
            max_hourly_namespace=max_entry.namespace,
            max_hourly_cost=max_entry.hourly_cost,
            min_hourly_namespace=min_entry.namespace,
            min_hourly_cost=min_entry.hourly_cost,
        )
