"""Cost velocity: rate of change in cost over a sliding window of snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class VelocityResult:
    """Per-namespace cost velocity (change per hour)."""

    namespace: str
    hourly_velocity: float  # $/h per hour  (acceleration in cost terms)
    monthly_velocity: float  # projected $/month per hour
    direction: str  # "rising", "falling", "stable"

    def __str__(self) -> str:
        sign = "+" if self.hourly_velocity >= 0 else ""
        return (
            f"{self.namespace}: {sign}{self.hourly_velocity:.6f} $/h per snapshot "
            f"({self.direction})"
        )


class CostVelocityAnalyzer:
    """Computes cost velocity from an ordered list of cost snapshots.

    Each element of *snapshots* is a list of :class:`NamespaceCost` objects
    representing one point in time.  Snapshots must be provided in
    chronological order (oldest first).
    """

    STABLE_THRESHOLD: float = 1e-9

    def __init__(self, snapshots: Optional[List[List[NamespaceCost]]] = None) -> None:
        self._snapshots: List[List[NamespaceCost]] = snapshots or []

    def add_snapshot(self, costs: List[NamespaceCost]) -> None:
        """Append a new cost snapshot (most recent)."""
        self._snapshots.append(costs)

    def analyze(self) -> List[VelocityResult]:
        """Return velocity results for all namespaces seen across snapshots.

        Requires at least two snapshots; returns an empty list otherwise.
        """
        if len(self._snapshots) < 2:
            return []

        # Build per-namespace time-series of hourly cost
        series: dict[str, List[float]] = {}
        for snapshot in self._snapshots:
            for nc in snapshot:
                series.setdefault(nc.namespace, []).append(nc.hourly_cost)

        results: List[VelocityResult] = []
        for namespace, values in sorted(series.items()):
            if len(values) < 2:
                velocity = 0.0
            else:
                # Linear regression slope via least-squares (simple form)
                n = len(values)
                xs = list(range(n))
                mean_x = sum(xs) / n
                mean_y = sum(values) / n
                num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
                den = sum((x - mean_x) ** 2 for x in xs)
                velocity = num / den if den != 0 else 0.0

            if abs(velocity) < self.STABLE_THRESHOLD:
                direction = "stable"
            elif velocity > 0:
                direction = "rising"
            else:
                direction = "falling"

            results.append(
                VelocityResult(
                    namespace=namespace,
                    hourly_velocity=velocity,
                    monthly_velocity=velocity * 720,
                    direction=direction,
                )
            )
        return results
