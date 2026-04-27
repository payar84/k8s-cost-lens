"""Compute simple cost trends from aggregated metrics windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.aggregator import AggregatedMetrics
from k8s_cost_lens.metrics.cost_estimator import CostEstimator, NamespaceCost


@dataclass
class NamespaceTrend:
    """Cost delta between two aggregation windows for a single namespace."""

    namespace: str
    previous_hourly_cost: float
    current_hourly_cost: float

    @property
    def delta(self) -> float:
        return self.current_hourly_cost - self.previous_hourly_cost

    @property
    def percent_change(self) -> Optional[float]:
        if self.previous_hourly_cost == 0:
            return None
        return (self.delta / self.previous_hourly_cost) * 100.0


class CostTrendAnalyzer:
    """Compare two aggregation windows and surface per-namespace cost trends."""

    def __init__(self, estimator: CostEstimator) -> None:
        self._estimator = estimator

    def _costs_by_namespace(
        self, window: List[AggregatedMetrics]
    ) -> dict[str, NamespaceCost]:
        from k8s_cost_lens.metrics.collector import NamespaceMetrics

        raw = [
            NamespaceMetrics(
                namespace=m.namespace,
                cpu_cores=m.avg_cpu_cores,
                memory_bytes=m.avg_memory_bytes,
            )
            for m in window
        ]
        return {c.namespace: c for c in self._estimator.estimate(raw)}

    def compare(
        self,
        previous: List[AggregatedMetrics],
        current: List[AggregatedMetrics],
    ) -> List[NamespaceTrend]:
        """Return trends for namespaces present in *current* window."""
        prev_costs = self._costs_by_namespace(previous)
        curr_costs = self._costs_by_namespace(current)

        trends: List[NamespaceTrend] = []
        for ns, curr in curr_costs.items():
            prev_hourly = prev_costs[ns].hourly_cost if ns in prev_costs else 0.0
            trends.append(
                NamespaceTrend(
                    namespace=ns,
                    previous_hourly_cost=prev_hourly,
                    current_hourly_cost=curr.hourly_cost,
                )
            )
        return sorted(trends, key=lambda t: t.namespace)
