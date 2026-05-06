"""Normalize namespace costs against a reference (e.g. cluster total or peak namespace)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class NormalizedCost:
    """A namespace cost expressed as a fraction of the reference value."""

    namespace: str
    hourly_cost: float
    monthly_cost: float
    hourly_share: float   # 0.0 – 1.0
    monthly_share: float  # 0.0 – 1.0
    reference_hourly: float
    reference_monthly: float

    def __str__(self) -> str:
        return (
            f"{self.namespace}: "
            f"{self.hourly_share * 100:.1f}% of reference "
            f"(${self.hourly_cost:.4f}/hr)"
        )


class CostNormalizer:
    """Normalize a list of :class:`NamespaceCost` entries against a reference.

    The reference can be:
    - ``'total'``  – sum of all namespace costs (default)
    - ``'peak'``   – the single most expensive namespace
    - a specific namespace name – costs are expressed relative to that namespace
    """

    def __init__(self, reference: str = "total") -> None:
        self.reference = reference

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def normalize(self, costs: List[NamespaceCost]) -> List[NormalizedCost]:
        """Return normalized costs.  Empty input returns empty list."""
        if not costs:
            return []

        ref_hourly, ref_monthly = self._reference_values(costs)

        results: List[NormalizedCost] = []
        for nc in costs:
            hourly_share = nc.hourly_cost / ref_hourly if ref_hourly else 0.0
            monthly_share = nc.monthly_cost / ref_monthly if ref_monthly else 0.0
            results.append(
                NormalizedCost(
                    namespace=nc.namespace,
                    hourly_cost=nc.hourly_cost,
                    monthly_cost=nc.monthly_cost,
                    hourly_share=hourly_share,
                    monthly_share=monthly_share,
                    reference_hourly=ref_hourly,
                    reference_monthly=ref_monthly,
                )
            )
        return results

    # ------------------------------------------------------------------
    # private
    # ------------------------------------------------------------------

    def _reference_values(self, costs: List[NamespaceCost]):
        if self.reference == "total":
            return (
                sum(c.hourly_cost for c in costs),
                sum(c.monthly_cost for c in costs),
            )
        if self.reference == "peak":
            peak = max(costs, key=lambda c: c.hourly_cost)
            return peak.hourly_cost, peak.monthly_cost
        # treat as namespace name
        match: Optional[NamespaceCost] = next(
            (c for c in costs if c.namespace == self.reference), None
        )
        if match is None:
            raise ValueError(
                f"Reference namespace '{self.reference}' not found in costs."
            )
        return match.hourly_cost, match.monthly_cost
