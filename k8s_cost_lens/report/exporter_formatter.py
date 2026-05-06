"""Formatter that renders Prometheus-style cost metrics as a readable table."""
from __future__ import annotations

from typing import List, Sequence

from k8s_cost_lens.metrics.cost_exporter import CostMetricsExporter, ExportedMetric
from k8s_cost_lens.metrics.cost_estimator import NamespaceCost

try:
    from tabulate import tabulate

    _TABULATE = True
except ImportError:  # pragma: no cover
    _TABULATE = False


class PrometheusMetricsFormatter:
    """Formats exported Prometheus metrics into human-readable tables or text."""

    def __init__(self, exporter: CostMetricsExporter | None = None) -> None:
        self._exporter = exporter or CostMetricsExporter()

    def _to_rows(self, metrics: Sequence[ExportedMetric]) -> List[List[str]]:
        rows = []
        for m in metrics:
            ns = m.labels.get("namespace", "")
            rows.append([ns, m.name, f"{m.value:.6f}"])
        return rows

    def as_table(self, costs: Sequence[NamespaceCost]) -> str:
        """Render metrics as an ASCII table."""
        metrics = self._exporter.export(costs)
        headers = ["Namespace", "Metric", "Value"]
        rows = self._to_rows(metrics)
        if not rows:
            return "No metrics to display."
        if _TABULATE:
            return tabulate(rows, headers=headers, tablefmt="github")
        header_line = "  ".join(f"{h:<35}" if i == 1 else f"{h:<20}" for i, h in enumerate(headers))
        separator = "-" * len(header_line)
        lines = [header_line, separator]
        for row in rows:
            lines.append(f"{row[0]:<20}  {row[1]:<35}  {row[2]}")
        return "\n".join(lines)

    def as_text(self, costs: Sequence[NamespaceCost]) -> str:
        """Return raw Prometheus text exposition format."""
        return self._exporter.as_text(costs)
