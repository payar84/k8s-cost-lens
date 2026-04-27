"""Formats cost estimation results into human-readable reports."""

from dataclasses import dataclass
from typing import List

from k8s_cost_lens.metrics.cost_estimator import NamespaceCost


@dataclass
class ReportRow:
    namespace: str
    cpu_cores: float
    memory_gib: float
    hourly_cost: float
    monthly_cost: float


class CostReportFormatter:
    """Renders a list of NamespaceCost objects as a formatted table or CSV."""

    _HEADER = (
        f"{'NAMESPACE':<30} {'CPU (cores)':>12} {'MEM (GiB)':>12}"
        f" {'HOURLY ($)':>12} {'MONTHLY ($)':>12}"
    )
    _DIVIDER = "-" * 80
    _ROW_FMT = "{:<30} {:>12.4f} {:>12.3f} {:>12.4f} {:>12.2f}"

    def _to_rows(self, costs: List[NamespaceCost]) -> List[ReportRow]:
        return [
            ReportRow(
                namespace=c.namespace,
                cpu_cores=c.cpu_cores,
                memory_gib=c.memory_bytes / (1024 ** 3),
                hourly_cost=c.hourly_cost,
                monthly_cost=c.monthly_cost,
            )
            for c in sorted(costs, key=lambda x: x.monthly_cost, reverse=True)
        ]

    def as_table(self, costs: List[NamespaceCost]) -> str:
        """Return a pretty-printed table string."""
        if not costs:
            return "No namespace cost data available."

        rows = self._to_rows(costs)
        lines = [self._HEADER, self._DIVIDER]
        for row in rows:
            lines.append(
                self._ROW_FMT.format(
                    row.namespace,
                    row.cpu_cores,
                    row.memory_gib,
                    row.hourly_cost,
                    row.monthly_cost,
                )
            )
        lines.append(self._DIVIDER)
        total_hourly = sum(r.hourly_cost for r in rows)
        total_monthly = sum(r.monthly_cost for r in rows)
        lines.append(
            self._ROW_FMT.format(
                "TOTAL", sum(r.cpu_cores for r in rows),
                sum(r.memory_gib for r in rows),
                total_hourly, total_monthly,
            )
        )
        return "\n".join(lines)

    def as_csv(self, costs: List[NamespaceCost]) -> str:
        """Return a CSV string with a header row."""
        rows = self._to_rows(costs)
        lines = ["namespace,cpu_cores,memory_gib,hourly_cost,monthly_cost"]
        for row in rows:
            lines.append(
                f"{row.namespace},{row.cpu_cores:.4f},{row.memory_gib:.3f}"
                f",{row.hourly_cost:.4f},{row.monthly_cost:.2f}"
            )
        return "\n".join(lines)
