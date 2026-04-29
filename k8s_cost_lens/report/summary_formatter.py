"""Formatter for a high-level cost summary across all namespaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from tabulate import tabulate

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class SummaryStats:
    total_namespaces: int
    total_hourly: float
    total_monthly: float
    top_namespace: str
    top_namespace_hourly: float
    avg_hourly: float


class CostSummaryFormatter:
    """Produces a single-table summary of cluster-wide cost metrics."""

    def __init__(self, costs: List[NamespaceCost]) -> None:
        self._costs = costs

    def _compute_stats(self) -> SummaryStats:
        if not self._costs:
            return SummaryStats(
                total_namespaces=0,
                total_hourly=0.0,
                total_monthly=0.0,
                top_namespace="—",
                top_namespace_hourly=0.0,
                avg_hourly=0.0,
            )
        total_hourly = sum(c.hourly_cost for c in self._costs)
        total_monthly = sum(c.monthly_cost for c in self._costs)
        top = max(self._costs, key=lambda c: c.hourly_cost)
        avg_hourly = total_hourly / len(self._costs)
        return SummaryStats(
            total_namespaces=len(self._costs),
            total_hourly=total_hourly,
            total_monthly=total_monthly,
            top_namespace=top.namespace,
            top_namespace_hourly=top.hourly_cost,
            avg_hourly=avg_hourly,
        )

    def as_table(self) -> str:
        """Return a human-readable summary table string."""
        stats = self._compute_stats()
        rows = [
            ["Namespaces tracked", stats.total_namespaces],
            ["Total hourly cost", f"${stats.total_hourly:.4f}"],
            ["Total monthly cost", f"${stats.total_monthly:.2f}"],
            ["Average hourly cost", f"${stats.avg_hourly:.4f}"],
            ["Top namespace", stats.top_namespace],
            ["Top namespace hourly", f"${stats.top_namespace_hourly:.4f}"],
        ]
        return tabulate(rows, headers=["Metric", "Value"], tablefmt="grid")

    def as_dict(self) -> dict:
        """Return summary stats as a plain dictionary."""
        stats = self._compute_stats()
        return {
            "total_namespaces": stats.total_namespaces,
            "total_hourly": round(stats.total_hourly, 6),
            "total_monthly": round(stats.total_monthly, 4),
            "avg_hourly": round(stats.avg_hourly, 6),
            "top_namespace": stats.top_namespace,
            "top_namespace_hourly": round(stats.top_namespace_hourly, 6),
        }
