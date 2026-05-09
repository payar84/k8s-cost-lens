"""Linear regression-based cost trend fitting for namespace spend forecasting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class RegressionResult:
    namespace: str
    slope_hourly: float        # $/hr change per snapshot interval
    intercept_hourly: float
    r_squared: float           # goodness of fit [0, 1]
    predicted_next_hourly: float
    predicted_next_monthly: float

    def __str__(self) -> str:
        direction = "rising" if self.slope_hourly > 0 else "falling" if self.slope_hourly < 0 else "flat"
        return (
            f"{self.namespace}: slope={self.slope_hourly:+.4f}/interval "
            f"R²={self.r_squared:.3f} ({direction})"
        )


def _linreg(xs: List[float], ys: List[float]) -> tuple[float, float, float]:
    """Return (slope, intercept, r_squared) for paired xs/ys."""
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0, 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    ss_yy = sum((y - mean_y) ** 2 for y in ys)
    if ss_xx == 0:
        return 0.0, mean_y, 0.0
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    r_squared = (ss_xy ** 2 / (ss_xx * ss_yy)) if ss_yy > 0 else 1.0
    return slope, intercept, r_squared


class CostRegressionAnalyzer:
    """Fits a linear model to historical per-namespace hourly costs."""

    _HOURS_PER_MONTH: float = 720.0

    def __init__(self) -> None:
        self._snapshots: List[List[NamespaceCost]] = []

    def add_snapshot(self, costs: List[NamespaceCost]) -> None:
        if costs:
            self._snapshots.append(list(costs))

    def analyze(self) -> List[RegressionResult]:
        if not self._snapshots:
            return []
        # Collect all namespace names seen
        ns_set: dict[str, List[Optional[float]]] = {}
        for snap in self._snapshots:
            for c in snap:
                ns_set.setdefault(c.namespace, [])
        # Build per-namespace time series (None if absent in a snapshot)
        n_snaps = len(self._snapshots)
        ns_series: dict[str, List[float]] = {ns: [] for ns in ns_set}
        for snap in self._snapshots:
            snap_map = {c.namespace: c.hourly_cost for c in snap}
            for ns in ns_set:
                ns_series[ns].append(snap_map.get(ns, 0.0))
        xs = list(range(n_snaps))
        results: List[RegressionResult] = []
        for ns, ys in ns_series.items():
            slope, intercept, r2 = _linreg(xs, ys)
            next_x = float(n_snaps)
            predicted_hourly = max(0.0, intercept + slope * next_x)
            results.append(RegressionResult(
                namespace=ns,
                slope_hourly=slope,
                intercept_hourly=intercept,
                r_squared=r2,
                predicted_next_hourly=predicted_hourly,
                predicted_next_monthly=predicted_hourly * self._HOURS_PER_MONTH,
            ))
        results.sort(key=lambda r: r.predicted_next_monthly, reverse=True)
        return results
