"""Baseline cost tracking: record a named snapshot of current costs for later comparison."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class BaselineEntry:
    namespace: str
    hourly_cost: float
    monthly_cost: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Baseline:
    name: str
    entries: List[BaselineEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get(self, namespace: str) -> Optional[BaselineEntry]:
        for entry in self.entries:
            if entry.namespace == namespace:
                return entry
        return None


@dataclass
class BaselineDiff:
    namespace: str
    baseline_hourly: float
    current_hourly: float
    baseline_monthly: float
    current_monthly: float

    @property
    def hourly_delta(self) -> float:
        return self.current_hourly - self.baseline_hourly

    @property
    def monthly_delta(self) -> float:
        return self.current_monthly - self.baseline_monthly

    @property
    def hourly_pct_change(self) -> Optional[float]:
        if self.baseline_hourly == 0.0:
            return None
        return (self.hourly_delta / self.baseline_hourly) * 100.0


class CostBaselineManager:
    def __init__(self) -> None:
        self._baselines: Dict[str, Baseline] = {}

    def record(self, name: str, costs: List[NamespaceCost]) -> Baseline:
        entries = [
            BaselineEntry(
                namespace=c.namespace,
                hourly_cost=c.hourly_cost,
                monthly_cost=c.monthly_cost,
            )
            for c in costs
        ]
        baseline = Baseline(name=name, entries=entries)
        self._baselines[name] = baseline
        return baseline

    def get(self, name: str) -> Optional[Baseline]:
        return self._baselines.get(name)

    def list_names(self) -> List[str]:
        return list(self._baselines.keys())

    def compare(self, name: str, current: List[NamespaceCost]) -> List[BaselineDiff]:
        baseline = self._baselines.get(name)
        if baseline is None:
            raise KeyError(f"No baseline named '{name}'")
        diffs: List[BaselineDiff] = []
        for cost in current:
            entry = baseline.get(cost.namespace)
            diffs.append(
                BaselineDiff(
                    namespace=cost.namespace,
                    baseline_hourly=entry.hourly_cost if entry else 0.0,
                    current_hourly=cost.hourly_cost,
                    baseline_monthly=entry.monthly_cost if entry else 0.0,
                    current_monthly=cost.monthly_cost,
                )
            )
        return diffs

    def delete(self, name: str) -> bool:
        if name in self._baselines:
            del self._baselines[name]
            return True
        return False
