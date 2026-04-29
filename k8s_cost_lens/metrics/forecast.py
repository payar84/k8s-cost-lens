"""Simple linear cost forecasting based on historical aggregated metrics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from k8s_cost_lens.metrics.aggregator import AggregatedMetrics
from k8s_cost_lens.metrics.cost_estimator import CostEstimator, NamespaceCost


@dataclass
class ForecastResult:
    namespace: str
    current_hourly: float
    forecasted_hourly: float
    forecasted_monthly: float
    slope: float  # $/hr change per interval

    @property
    def trend_direction(self) -> str:
        if self.slope > 0:
            return "increasing"
        if self.slope < 0:
            return "decreasing"
        return "stable"


class CostForecaster:
    """Fits a least-squares linear trend over a sequence of cost snapshots
    and projects one *forecast_intervals* step ahead."""

    def __init__(self, estimator: CostEstimator, forecast_intervals: int = 1) -> None:
        if forecast_intervals < 1:
            raise ValueError("forecast_intervals must be >= 1")
        self._estimator = estimator
        self._forecast_intervals = forecast_intervals
        self._history: List[List[NamespaceCost]] = []

    def add_snapshot(self, aggregated: List[AggregatedMetrics]) -> None:
        """Compute costs for *aggregated* and append to internal history."""
        costs = [self._estimator.estimate(a) for a in aggregated]
        self._history.append(costs)

    def forecast(self) -> List[ForecastResult]:
        """Return per-namespace forecasts.  Requires at least one snapshot."""
        if not self._history:
            return []

        # Collect all namespace names seen across all snapshots
        namespaces: dict[str, List[Optional[float]]] = {}
        for snapshot in self._history:
            for cost in snapshot:
                namespaces.setdefault(cost.namespace, [])

        # Build time-series per namespace (None when absent in a snapshot)
        ns_series: dict[str, List[float]] = {ns: [] for ns in namespaces}
        for snapshot in self._history:
            present = {c.namespace: c.hourly_cost for c in snapshot}
            for ns in namespaces:
                ns_series[ns].append(present.get(ns, 0.0))

        results: List[ForecastResult] = []
        n = len(self._history)
        xs = list(range(n))
        x_mean = sum(xs) / n

        for ns, ys in ns_series.items():
            y_mean = sum(ys) / n
            denom = sum((x - x_mean) ** 2 for x in xs)
            slope = (
                sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n)) / denom
                if denom != 0
                else 0.0
            )
            current = ys[-1]
            forecasted_hourly = max(0.0, current + slope * self._forecast_intervals)
            results.append(
                ForecastResult(
                    namespace=ns,
                    current_hourly=current,
                    forecasted_hourly=forecasted_hourly,
                    forecasted_monthly=forecasted_hourly * 720,
                    slope=slope,
                )
            )

        results.sort(key=lambda r: r.namespace)
        return results
