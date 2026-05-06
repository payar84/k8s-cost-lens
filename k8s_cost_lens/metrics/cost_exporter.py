"""Prometheus-style cost metrics exporter for k8s-cost-lens."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class ExportedMetric:
    """A single Prometheus-style metric line."""

    name: str
    labels: dict
    value: float

    def __str__(self) -> str:
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        return f"{self.name}{{{label_str}}} {self.value}"


@dataclass
class CostMetricsExporter:
    """Converts NamespaceCost list into Prometheus exposition format lines."""

    prefix: str = "k8s_cost_lens"
    extra_labels: dict = field(default_factory=dict)

    def export(self, costs: Sequence[NamespaceCost]) -> List[ExportedMetric]:
        """Return ExportedMetric objects for each namespace cost entry."""
        metrics: List[ExportedMetric] = []
        for cost in costs:
            base_labels = {"namespace": cost.namespace, **self.extra_labels}
            metrics.append(
                ExportedMetric(
                    name=f"{self.prefix}_hourly_cost_usd",
                    labels=base_labels,
                    value=round(cost.hourly_cost, 6),
                )
            )
            metrics.append(
                ExportedMetric(
                    name=f"{self.prefix}_monthly_cost_usd",
                    labels=base_labels,
                    value=round(cost.monthly_cost, 6),
                )
            )
        return metrics

    def as_text(self, costs: Sequence[NamespaceCost]) -> str:
        """Render metrics in Prometheus text exposition format."""
        metrics = self.export(costs)
        lines: List[str] = []
        seen_names: set = set()
        for m in metrics:
            if m.name not in seen_names:
                lines.append(f"# HELP {m.name} Cost in USD")
                lines.append(f"# TYPE {m.name} gauge")
                seen_names.add(m.name)
            lines.append(str(m))
        return "\n".join(lines)
