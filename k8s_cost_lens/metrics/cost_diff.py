"""Point-in-time cost diff between two snapshots of namespace costs.

Provides CostDiffAnalyzer which compares two lists of NamespaceCost objects
(e.g. current vs. previous poll) and produces per-namespace deltas with
percentage change and a direction indicator.  Useful for the watch-loop
dashboard to highlight namespaces whose spend is moving significantly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass(frozen=True)
class CostDiff:
    """Cost difference for a single namespace between two points in time."""

    namespace: str
    prev_hourly: float
    curr_hourly: float
    prev_monthly: float
    curr_monthly: float

    @property
    def hourly_delta(self) -> float:
        """Absolute change in hourly cost (curr - prev)."""
        return self.curr_hourly - self.prev_hourly

    @property
    def monthly_delta(self) -> float:
        """Absolute change in monthly cost (curr - prev)."""
        return self.curr_monthly - self.prev_monthly

    @property
    def hourly_pct_change(self) -> Optional[float]:
        """Percentage change in hourly cost, or None when prev is zero."""
        if self.prev_hourly == 0.0:
            return None
        return (self.hourly_delta / self.prev_hourly) * 100.0

    @property
    def monthly_pct_change(self) -> Optional[float]:
        """Percentage change in monthly cost, or None when prev is zero."""
        if self.prev_monthly == 0.0:
            return None
        return (self.monthly_delta / self.prev_monthly) * 100.0

    @property
    def direction(self) -> str:
        """Unicode arrow indicating cost movement: ↑ up, ↓ down, → flat."""
        if self.hourly_delta > 0:
            return "\u2191"  # ↑
        if self.hourly_delta < 0:
            return "\u2193"  # ↓
        return "\u2192"  # →

    def __str__(self) -> str:
        pct = self.hourly_pct_change
        pct_str = f"{pct:+.1f}%" if pct is not None else "n/a"
        return (
            f"{self.namespace}: {self.direction} "
            f"hourly ${self.curr_hourly:.4f} ({pct_str})"
        )


class CostDiffAnalyzer:
    """Compares two cost snapshots and returns per-namespace CostDiff objects.

    Namespaces present only in *before* are reported with a current cost of 0.
    Namespaces present only in *after* are reported with a previous cost of 0.
    """

    def diff(
        self,
        before: Sequence[NamespaceCost],
        after: Sequence[NamespaceCost],
    ) -> List[CostDiff]:
        """Return a list of :class:`CostDiff` for every namespace seen in
        either snapshot, sorted alphabetically by namespace name.

        Args:
            before: Cost snapshot taken at the earlier point in time.
            after:  Cost snapshot taken at the later point in time.

        Returns:
            Sorted list of :class:`CostDiff` instances.
        """
        prev_map: Dict[str, NamespaceCost] = {c.namespace: c for c in before}
        curr_map: Dict[str, NamespaceCost] = {c.namespace: c for c in after}

        all_namespaces = sorted(prev_map.keys() | curr_map.keys())

        results: List[CostDiff] = []
        for ns in all_namespaces:
            prev = prev_map.get(ns)
            curr = curr_map.get(ns)

            results.append(
                CostDiff(
                    namespace=ns,
                    prev_hourly=prev.hourly_cost if prev else 0.0,
                    curr_hourly=curr.hourly_cost if curr else 0.0,
                    prev_monthly=prev.monthly_cost if prev else 0.0,
                    curr_monthly=curr.monthly_cost if curr else 0.0,
                )
            )

        return results
