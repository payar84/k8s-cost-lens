"""Anomaly detection for namespace cost metrics using simple z-score analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import statistics

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class AnomalyResult:
    namespace: str
    hourly_cost: float
    mean_hourly: float
    stddev_hourly: float
    z_score: Optional[float]
    is_anomaly: bool

    def __str__(self) -> str:
        flag = "[ANOMALY]" if self.is_anomaly else "[OK]"
        z = f"{self.z_score:.2f}" if self.z_score is not None else "N/A"
        return (
            f"{flag} {self.namespace}: hourly=${self.hourly_cost:.4f} "
            f"(mean=${self.mean_hourly:.4f}, z={z})"
        )


@dataclass
class CostAnomalyDetector:
    """Detects anomalous namespace costs relative to a historical baseline.

    A namespace is flagged when its z-score exceeds *threshold* standard
    deviations from the mean of the provided baseline costs.
    """

    threshold: float = 2.0
    _baseline: List[float] = field(default_factory=list, init=False, repr=False)

    def fit(self, historical_costs: List[NamespaceCost]) -> None:
        """Store hourly costs from a historical snapshot as the baseline."""
        self._baseline = [c.hourly_cost for c in historical_costs]

    def detect(self, current_costs: List[NamespaceCost]) -> List[AnomalyResult]:
        """Return an AnomalyResult for every namespace in *current_costs*."""
        if len(self._baseline) < 2:
            mean = self._baseline[0] if self._baseline else 0.0
            stddev = 0.0
            results = []
            for nc in current_costs:
                results.append(
                    AnomalyResult(
                        namespace=nc.namespace,
                        hourly_cost=nc.hourly_cost,
                        mean_hourly=mean,
                        stddev_hourly=stddev,
                        z_score=None,
                        is_anomaly=False,
                    )
                )
            return results

        mean = statistics.mean(self._baseline)
        stddev = statistics.stdev(self._baseline)
        results = []
        for nc in current_costs:
            if stddev == 0.0:
                z_score: Optional[float] = None
                is_anomaly = False
            else:
                z_score = (nc.hourly_cost - mean) / stddev
                is_anomaly = abs(z_score) >= self.threshold
            results.append(
                AnomalyResult(
                    namespace=nc.namespace,
                    hourly_cost=nc.hourly_cost,
                    mean_hourly=mean,
                    stddev_hourly=stddev,
                    z_score=z_score,
                    is_anomaly=is_anomaly,
                )
            )
        return results

    def anomalies_only(self, current_costs: List[NamespaceCost]) -> List[AnomalyResult]:
        """Convenience wrapper — returns only flagged anomalies."""
        return [r for r in self.detect(current_costs) if r.is_anomaly]
