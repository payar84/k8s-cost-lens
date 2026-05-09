"""Per-namespace cost percentile ranking across a collection of cost snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class PercentileResult:
    namespace: str
    hourly_cost: float
    monthly_cost: float
    hourly_percentile: float   # 0-100
    monthly_percentile: float  # 0-100

    def __str__(self) -> str:
        return (
            f"{self.namespace}: "
            f"hourly=${self.hourly_cost:.4f} (p{self.hourly_percentile:.1f}), "
            f"monthly=${self.monthly_cost:.2f} (p{self.monthly_percentile:.1f})"
        )


def _percentile_rank(value: float, all_values: List[float]) -> float:
    """Return the percentile rank (0-100) of *value* within *all_values*."""
    if not all_values:
        return 0.0
    n = len(all_values)
    below = sum(1 for v in all_values if v < value)
    equal = sum(1 for v in all_values if v == value)
    # mid-point formula: (below + 0.5 * equal) / n * 100
    return (below + 0.5 * equal) / n * 100.0


class CostPercentileAnalyzer:
    """Rank each namespace by its cost percentile relative to all other namespaces."""

    def analyze(self, costs: List[NamespaceCost]) -> List[PercentileResult]:
        """Return a :class:`PercentileResult` for every entry in *costs*."""
        if not costs:
            return []

        hourly_values = [c.hourly_cost for c in costs]
        monthly_values = [c.monthly_cost for c in costs]

        results: List[PercentileResult] = []
        for c in costs:
            results.append(
                PercentileResult(
                    namespace=c.namespace,
                    hourly_cost=c.hourly_cost,
                    monthly_cost=c.monthly_cost,
                    hourly_percentile=_percentile_rank(c.hourly_cost, hourly_values),
                    monthly_percentile=_percentile_rank(c.monthly_cost, monthly_values),
                )
            )
        return results
