"""Sort and rank namespace costs by various criteria."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


class SortKey(str, Enum):
    HOURLY = "hourly"
    MONTHLY = "monthly"
    CPU = "cpu"
    MEMORY = "memory"
    NAMESPACE = "namespace"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class RankedCost:
    rank: int
    cost: NamespaceCost

    def __str__(self) -> str:
        return f"#{self.rank} {self.cost.namespace} (${self.cost.hourly_cost:.4f}/hr)"


class CostSorter:
    """Sorts and ranks a list of NamespaceCost objects."""

    def __init__(
        self,
        key: SortKey = SortKey.MONTHLY,
        order: SortOrder = SortOrder.DESC,
        top_n: int | None = None,
    ) -> None:
        self.key = key
        self.order = order
        self.top_n = top_n

    def _get_value(self, cost: NamespaceCost) -> float | str:
        if self.key == SortKey.HOURLY:
            return cost.hourly_cost
        if self.key == SortKey.MONTHLY:
            return cost.monthly_cost
        if self.key == SortKey.CPU:
            return cost.cpu_cost
        if self.key == SortKey.MEMORY:
            return cost.memory_cost
        return cost.namespace  # SortKey.NAMESPACE

    def sort(self, costs: List[NamespaceCost]) -> List[RankedCost]:
        """Return a ranked, sorted list of costs."""
        reverse = self.order == SortOrder.DESC
        sorted_costs = sorted(costs, key=self._get_value, reverse=reverse)
        if self.top_n is not None:
            sorted_costs = sorted_costs[: self.top_n]
        return [
            RankedCost(rank=i + 1, cost=c) for i, c in enumerate(sorted_costs)
        ]
