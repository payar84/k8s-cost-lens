"""Top-N namespace cost ranking by hourly or monthly spend."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


class TopNMetric(str, Enum):
    HOURLY = "hourly"
    MONTHLY = "monthly"


@dataclass
class TopNResult:
    rank: int
    namespace: str
    hourly_cost: float
    monthly_cost: float

    def __str__(self) -> str:
        return (
            f"#{self.rank} {self.namespace}: "
            f"${self.hourly_cost:.4f}/hr  ${self.monthly_cost:.2f}/mo"
        )


class CostTopNAnalyzer:
    """Return the top-N (or bottom-N) namespaces by cost."""

    def __init__(
        self,
        n: int = 5,
        metric: TopNMetric = TopNMetric.MONTHLY,
        ascending: bool = False,
    ) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        self._n = n
        self._metric = metric
        self._ascending = ascending

    def top(self, costs: List[NamespaceCost]) -> List[TopNResult]:
        """Return up to *n* results ranked by the chosen metric."""
        if not costs:
            return []

        key = (
            (lambda c: c.hourly_cost)
            if self._metric == TopNMetric.HOURLY
            else (lambda c: c.monthly_cost)
        )

        sorted_costs = sorted(costs, key=key, reverse=not self._ascending)
        selected = sorted_costs[: self._n]

        return [
            TopNResult(
                rank=idx + 1,
                namespace=c.namespace,
                hourly_cost=c.hourly_cost,
                monthly_cost=c.monthly_cost,
            )
            for idx, c in enumerate(selected)
        ]
