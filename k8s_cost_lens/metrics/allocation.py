"""Per-namespace cost allocation with configurable weight factors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class AllocationWeights:
    """Relative weights used when splitting shared costs."""

    cpu_weight: float = 0.5
    memory_weight: float = 0.5

    def __post_init__(self) -> None:
        total = self.cpu_weight + self.memory_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"cpu_weight + memory_weight must equal 1.0, got {total}"
            )


@dataclass
class AllocationResult:
    """Allocated cost share for a single namespace."""

    namespace: str
    allocated_hourly: float
    allocated_monthly: float
    share_pct: float  # 0-100

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{self.namespace}: {self.share_pct:.1f}% "
            f"(${self.allocated_hourly:.4f}/hr, ${self.allocated_monthly:.2f}/mo)"
        )


class CostAllocator:
    """Allocates a shared cost pool across namespaces by weighted resource usage."""

    def __init__(self, weights: Optional[AllocationWeights] = None) -> None:
        self._weights = weights or AllocationWeights()

    def allocate(self, costs: List[NamespaceCost]) -> List[AllocationResult]:
        """Return per-namespace allocation results."""
        if not costs:
            return []

        total_cpu = sum(c.cpu_cores for c in costs)
        total_mem = sum(c.memory_bytes for c in costs)
        total_hourly = sum(c.hourly_cost for c in costs)
        total_monthly = sum(c.monthly_cost for c in costs)

        results: List[AllocationResult] = []
        for cost in costs:
            cpu_share = (cost.cpu_cores / total_cpu) if total_cpu > 0 else 0.0
            mem_share = (cost.memory_bytes / total_mem) if total_mem > 0 else 0.0

            weighted_share = (
                self._weights.cpu_weight * cpu_share
                + self._weights.memory_weight * mem_share
            )

            results.append(
                AllocationResult(
                    namespace=cost.namespace,
                    allocated_hourly=total_hourly * weighted_share,
                    allocated_monthly=total_monthly * weighted_share,
                    share_pct=weighted_share * 100.0,
                )
            )

        return results
