"""Detect sudden cost spikes between two consecutive snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class SpikeResult:
    namespace: str
    previous_hourly: float
    current_hourly: float
    previous_monthly: float
    current_monthly: float
    hourly_delta: float
    monthly_delta: float
    hourly_pct_change: Optional[float]  # None when previous is zero
    threshold_pct: float
    is_spike: bool

    def __str__(self) -> str:
        pct = (
            f"{self.hourly_pct_change:+.1f}%"
            if self.hourly_pct_change is not None
            else "N/A"
        )
        return (
            f"{self.namespace}: hourly {self.previous_hourly:.4f} -> "
            f"{self.current_hourly:.4f} ({pct})"
        )


class CostSpikeDetector:
    """Compare two lists of NamespaceCost and flag namespaces whose hourly
    cost grew by more than *threshold_pct* percent."""

    def __init__(self, threshold_pct: float = 50.0) -> None:
        if threshold_pct < 0:
            raise ValueError("threshold_pct must be >= 0")
        self.threshold_pct = threshold_pct

    def detect(
        self,
        previous: List[NamespaceCost],
        current: List[NamespaceCost],
    ) -> List[SpikeResult]:
        """Return a SpikeResult for every namespace present in *current*."""
        prev_map = {c.namespace: c for c in previous}
        results: List[SpikeResult] = []

        for cur in current:
            prev = prev_map.get(cur.namespace)
            prev_hourly = prev.hourly_cost if prev is not None else 0.0
            prev_monthly = prev.monthly_cost if prev is not None else 0.0

            hourly_delta = cur.hourly_cost - prev_hourly
            monthly_delta = cur.monthly_cost - prev_monthly

            if prev_hourly == 0.0:
                hourly_pct_change: Optional[float] = None
                is_spike = cur.hourly_cost > 0.0
            else:
                hourly_pct_change = (hourly_delta / prev_hourly) * 100.0
                is_spike = hourly_pct_change > self.threshold_pct

            results.append(
                SpikeResult(
                    namespace=cur.namespace,
                    previous_hourly=prev_hourly,
                    current_hourly=cur.hourly_cost,
                    previous_monthly=prev_monthly,
                    current_monthly=cur.monthly_cost,
                    hourly_delta=hourly_delta,
                    monthly_delta=monthly_delta,
                    hourly_pct_change=hourly_pct_change,
                    threshold_pct=self.threshold_pct,
                    is_spike=is_spike,
                )
            )

        return results

    def spikes_only(self, results: List[SpikeResult]) -> List[SpikeResult]:
        """Filter to only results that are flagged as spikes."""
        return [r for r in results if r.is_spike]
