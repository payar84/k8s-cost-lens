"""Aggregates namespace metrics across multiple collection windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from k8s_cost_lens.metrics.collector import NamespaceMetrics


@dataclass
class AggregatedMetrics:
    """Rolling average of resource usage for a namespace."""

    namespace: str
    avg_cpu_cores: float
    avg_memory_bytes: float
    sample_count: int


class MetricsAggregator:
    """Accumulates NamespaceMetrics snapshots and computes rolling averages."""

    def __init__(self) -> None:
        self._samples: Dict[str, List[NamespaceMetrics]] = {}

    def add_snapshot(self, metrics: List[NamespaceMetrics]) -> None:
        """Record a new collection snapshot."""
        for nm in metrics:
            self._samples.setdefault(nm.namespace, []).append(nm)

    def aggregate(self) -> List[AggregatedMetrics]:
        """Return averaged metrics for every namespace seen so far."""
        result: List[AggregatedMetrics] = []
        for namespace, samples in self._samples.items():
            count = len(samples)
            avg_cpu = sum(s.cpu_cores for s in samples) / count
            avg_mem = sum(s.memory_bytes for s in samples) / count
            result.append(
                AggregatedMetrics(
                    namespace=namespace,
                    avg_cpu_cores=avg_cpu,
                    avg_memory_bytes=avg_mem,
                    sample_count=count,
                )
            )
        return sorted(result, key=lambda x: x.namespace)

    def clear(self) -> None:
        """Reset all accumulated samples."""
        self._samples.clear()

    @property
    def namespace_count(self) -> int:
        return len(self._samples)
